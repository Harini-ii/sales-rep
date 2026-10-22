"""
Batch Upload Script for Aircraft Images to Cloudflare R2 and PostgreSQL.

This script:
1. Connects to Cloudflare R2 bucket `helightjet` via S3 API with SigV4.
2. Connects to PostgreSQL database table `sales_hj.aircraft_images`.
3. Optionally removes legacy/dummy test records (e.g., IMG-001..IMG-004).
4. Scans all 670 aircraft images from `image_assets/` (ImageA through ImagesF).
5. Concurrently uploads each image to Cloudflare R2 with:
   - Key: {uuid}.{ext}
   - Content-Type: appropriate image MIME type
   - Cache-Control: public, max-age=31536000, immutable
6. Inserts the metadata record into `sales_hj.aircraft_images`:
   - image_id: UUID v4 string
   - image_name: Descriptive aircraft title (e.g., 'Hawker 400A XP Midsize Jet (ImageA) - Image 01')
   - image_url: https://pub-43941128fd0b4687871df42e46dcc8f6.r2.dev/{uuid}.{ext}
   - category: ImageA..ImagesF
   - aircraft_model: folder name
   - file_format: jpg, png, webp, jfif, etc.
   - r2_key: {uuid}.{ext}
   - is_active: True
7. Validates public access to uploaded images.
"""

import os
import sys
import uuid
import ssl
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.config import Config
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import (
    R2_BUCKET_NAME,
    R2_ENDPOINT_URL,
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_PUBLIC_DOMAIN,
    DATABASE_URL,
)
from app.models.image import AircraftImage

# MIME type mapping
MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "jfif": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "avif": "image/avif",
}


def get_s3_client():
    if not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
        raise ValueError("R2_ACCESS_KEY_ID or R2_SECRET_ACCESS_KEY not configured in .env")

    return boto3.client(
        service_name="s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4", max_pool_connections=25),
        region_name="auto",
    )


def collect_images(assets_dir: Path):
    """
    Collect and sort all image assets into structured records.
    """
    all_items = []
    for root, dirs, files in os.walk(assets_dir):
        for f in sorted(files):
            if f.startswith(".") or f.startswith("Thumbs.db"):
                continue
            full_path = Path(root) / f
            rel = full_path.relative_to(assets_dir)
            parts = rel.parts
            if len(parts) < 2:
                continue

            category = parts[0]
            aircraft_model = parts[-2]
            ext = full_path.suffix.lower().lstrip(".")

            all_items.append({
                "full_path": full_path,
                "relative_path": str(rel),
                "category": category,
                "aircraft_model": aircraft_model,
                "filename": f,
                "file_format": ext,
            })

    # Group and assign descriptive, unique image_name and UUID
    model_cat_counts = defaultdict(int)
    for item in all_items:
        key = (item["category"], item["aircraft_model"])
        model_cat_counts[key] += 1
        idx = model_cat_counts[key]
        image_uuid = str(uuid.uuid4())
        r2_key = f"{image_uuid}.{item['file_format']}"

        pub_base = (R2_PUBLIC_DOMAIN or "").rstrip("/")
        image_url = f"{pub_base}/{r2_key}"
        image_name = f"{item['aircraft_model']} ({item['category']}) - Image {idx:02d}"

        item["image_id"] = image_uuid
        item["r2_key"] = r2_key
        item["image_url"] = image_url
        item["image_name"] = image_name

    return all_items


import threading

_thread_local = threading.local()

def get_thread_s3_client():
    if not hasattr(_thread_local, "s3_client"):
        _thread_local.s3_client = get_s3_client()
    return _thread_local.s3_client


def upload_single_image(item: dict, bucket_name: str):
    """
    Read local image file bytes and upload to Cloudflare R2 bucket.
    """
    s3_client = get_thread_s3_client()
    ext = item["file_format"]
    content_type = MIME_MAP.get(ext, "application/octet-stream")

    with open(item["full_path"], "rb") as f:
        file_bytes = f.read()

    s3_client.put_object(
        Bucket=bucket_name,
        Key=item["r2_key"],
        Body=file_bytes,
        ContentType=content_type,
        CacheControl="public, max-age=31536000, immutable",
    )
    return item


def main():
    print("=" * 70)
    print("  Helite Jet - Cloudflare R2 & PostgreSQL Image Batch Upload")
    print("=" * 70)
    print(f"Bucket:         {R2_BUCKET_NAME}")
    print(f"Public Domain:  {R2_PUBLIC_DOMAIN}")
    print(f"Endpoint:       {R2_ENDPOINT_URL}")
    print(f"Database:       {DATABASE_URL.split('@')[-1] if DATABASE_URL else 'Not set'}")
    print("-" * 70)

    # 1. Initialize DB Session
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 2. Initialize S3 client
    s3_client = get_s3_client()

    # Verify R2 connection
    print("Testing R2 Bucket Connectivity...")
    res = s3_client.list_objects_v2(Bucket=R2_BUCKET_NAME, MaxKeys=5)
    print(f"✅ R2 Connected! Current objects in bucket: {res.get('KeyCount', 0)}")

    # 3. Clean legacy test rows
    legacy_rows = db.query(AircraftImage).filter(AircraftImage.image_id.like("IMG-%")).all()
    if legacy_rows:
        print(f"Found {len(legacy_rows)} legacy dummy records (IMG-xxx). Cleaning them up...")
        for r in legacy_rows:
            db.delete(r)
        db.commit()
        print("✅ Legacy records cleaned from sales_hj.AIRCRAFT_IMAGES_HJ.")

    # 4. Check existing DB records
    existing_urls = set(k[0] for k in db.query(AircraftImage.image_url).all() if k[0])
    existing_names = set(k[0] for k in db.query(AircraftImage.image_name).all() if k[0])
    print(f"Existing rows in sales_hj.AIRCRAFT_IMAGES_HJ: {len(existing_names)}")

    # 5. Scan image_assets
    assets_dir = BASE_DIR / "image_assets"
    items = collect_images(assets_dir)
    print(f"Total images collected from {assets_dir.name}: {len(items)}")

    # Filter out any that were already inserted
    items_to_upload = [
        it for it in items
        if it["image_url"] not in existing_urls and it["image_name"] not in existing_names
    ]
    print(f"New images to upload and register: {len(items_to_upload)}")

    if not items_to_upload:
        print("✅ All images are already uploaded and recorded in the database!")
        return

    # 6. Concurrently upload to Cloudflare R2
    print(f"\nUploading {len(items_to_upload)} files to Cloudflare R2 with 12 workers...")
    start_time = time.time()
    uploaded_items = []
    errors = []

    with ThreadPoolExecutor(max_workers=12) as executor:
        future_to_item = {
            executor.submit(upload_single_image, item, R2_BUCKET_NAME): item
            for item in items_to_upload
        }

        completed = 0
        total = len(items_to_upload)
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                uploaded_items.append(result)
                completed += 1
                if completed % 50 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    speed = completed / elapsed if elapsed > 0 else 0
                    print(f"  [{completed}/{total}] uploaded ({speed:.1f} files/sec)...")
            except Exception as e:
                errors.append((item["relative_path"], str(e)))
                print(f"  ❌ Error uploading {item['relative_path']}: {e}")

    upload_duration = time.time() - start_time
    print(f"\n✅ Finished R2 uploads in {upload_duration:.1f} seconds! (Success: {len(uploaded_items)}, Errors: {len(errors)})")

    if errors:
        print(f"⚠️ {len(errors)} files failed to upload. Halting database insertion for safety.")
        sys.exit(1)

    # 7. Insert metadata into PostgreSQL in batch
    print(f"\nRegistering {len(uploaded_items)} image records into sales_hj.AIRCRAFT_IMAGES_HJ...")
    now = datetime.now(timezone.utc)
    new_db_records = [
        AircraftImage(
            image_id=item["image_id"],
            image_name=item["image_name"],
            image_url=item["image_url"],
            category=item["category"],
            aircraft_model=item["aircraft_model"],
            file_format=item["file_format"],
            # r2_key=item["r2_key"],
            created_at=now,
            is_active=True,
        )
        for item in uploaded_items
    ]

    db.bulk_save_objects(new_db_records)
    db.commit()
    print("✅ All records successfully committed to PostgreSQL!")

    # 8. Verification
    total_db_count = db.query(func.count(AircraftImage.image_id)).scalar()
    print(f"\nTotal active records in sales_hj.aircraft_images: {total_db_count}")

    # Test downloading sample image from public CDN URL
    sample = uploaded_items[0]
    sample_url = sample["image_url"]
    print(f"\nVerifying public CDN URL: {sample_url}")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(sample_url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"  ✅ CDN Public URL returned status: {resp.status}")
            print(f"  ✅ Content-Type: {resp.headers.get('Content-Type')}")
            print(f"  ✅ Downloaded Bytes: {len(resp.read())}")
    except Exception as e:
        print(f"  ❌ Error testing CDN URL: {e}")

    db.close()
    print("\n🎉 Batch upload and PostgreSQL registration complete!")


if __name__ == "__main__":
    main()
