"""
Cloudflare R2 Integration Service for Helite Jet Sales Dashboard.

This service manages Cloudflare R2 bucket configuration and S3-compatible integration.
Security Note: Credentials and secret keys are never hardcoded or exposed in logs/responses.
"""

from typing import Dict, Any, List
from fastapi import HTTPException, status
from app.config import (
    R2_BUCKET_NAME,
    R2_ENDPOINT_URL,
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_PUBLIC_DOMAIN,
)


def get_r2_status() -> Dict[str, Any]:
    """
    Evaluates current R2 configuration readiness without exposing secret values.
    Returns status flags and identifies missing configuration items.
    """
    missing: List[str] = []
    if not R2_ACCESS_KEY_ID:
        missing.append("R2_ACCESS_KEY_ID")
    if not R2_SECRET_ACCESS_KEY:
        missing.append("R2_SECRET_ACCESS_KEY")
    if not R2_PUBLIC_DOMAIN:
        missing.append("R2_PUBLIC_DOMAIN (public image/CDN domain)")

    is_ready = len(missing) == 0

    if is_ready:
        notes = "Cloudflare R2 is fully configured for S3 API uploads and public image delivery."
    else:
        notes = (
            f"Cloudflare R2 bucket '{R2_BUCKET_NAME}' and S3 endpoint are configured in .env, "
            f"but credentials ({', '.join(missing)}) are missing. "
            "S3 endpoint is for internal API calls, not direct browser viewing. "
            "Direct uploads will be enabled once access keys and public domain are supplied."
        )

    return {
        "configured": is_ready,
        "bucket_name": R2_BUCKET_NAME,
        "endpoint_url": R2_ENDPOINT_URL,
        "has_access_key": bool(R2_ACCESS_KEY_ID),
        "has_secret_key": bool(R2_SECRET_ACCESS_KEY),
        "has_public_domain": bool(R2_PUBLIC_DOMAIN),
        "missing_configurations": missing,
        "notes": notes,
    }


def upload_image_to_r2(
    file_bytes: bytes,
    filename: str,
    content_type: str = "image/jpeg"
) -> str:
    """
    Prepared upload function for Cloudflare R2 bucket.
    Validates credentials prior to attempting upload.
    Raises HTTPException if credentials or SDK are unavailable.
    """
    if not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Cloudflare R2 upload is unavailable: R2_ACCESS_KEY_ID and "
                "R2_SECRET_ACCESS_KEY are not configured in environment."
            )
        )

    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="boto3 library is required for R2 direct uploads but is not installed."
        )

    s3_client = boto3.client(
        service_name="s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )

    s3_client.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=filename,
        Body=file_bytes,
        ContentType=content_type
    )

    if R2_PUBLIC_DOMAIN:
        base = R2_PUBLIC_DOMAIN.rstrip("/")
        return f"{base}/{filename}"

    return f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{filename}"
