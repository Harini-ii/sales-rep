import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.image import ImageCreate, ImageRecord, R2StatusResponse
from app.services.r2_service import get_r2_status
from app.database import get_db
from app.models.image import AircraftImage

router = APIRouter(
    prefix="/images",
    tags=["Images"]
)


def _to_image_record(record: AircraftImage) -> ImageRecord:
    """Helper to convert SQLAlchemy AircraftImage to ImageRecord schema."""
    return ImageRecord(
        image_id=str(record.image_id),
        image_name=record.image_name,
        image_url=record.image_url,
        category=record.category,
        aircraft_model=record.aircraft_model,
        file_format=record.file_format,
        # r2_key=record.r2_key,
        created_at=record.created_at,
        storage_type="postgresql",
        is_persisted_to_db=True,
        note="Persisted in PostgreSQL database (sales_hj.AIRCRAFT_IMAGES_HJ)."
    )


@router.get("/r2/status", response_model=R2StatusResponse, status_code=status.HTTP_200_OK)
def check_r2_configuration():
    """
    Check Cloudflare R2 bucket configuration and readiness.
    Safely verifies whether required credentials and public domain are present
    without exposing any secret values.
    """
    return get_r2_status()


@router.post("/", response_model=ImageRecord, status_code=status.HTTP_201_CREATED)
def create_image(image_data: ImageCreate, db: Session = Depends(get_db)):
    """
    Register a new aircraft image record in PostgreSQL (sales_hj.aircraft_images).
    Validates against duplicate image names or URLs.
    Errors are explicit; no silent fallback to in-memory storage.
    """
    try:
        trimmed_name = image_data.image_name.strip()
        str_url = str(image_data.image_url).strip()

        # Check for duplicates in PostgreSQL
        existing_name = db.query(AircraftImage).filter(
            func.lower(AircraftImage.image_name) == trimmed_name.lower(),
            AircraftImage.is_active == True
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An image with name '{trimmed_name}' already exists in the database."
            )

        existing_url = db.query(AircraftImage).filter(
            AircraftImage.image_url == str_url,
            AircraftImage.is_active == True
        ).first()
        if existing_url:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An image with URL '{str_url}' already exists in the database."
            )

        # Generate UUID for image_id
        new_image_id = str(uuid.uuid4())

        new_image = AircraftImage(
            image_id=new_image_id,
            image_name=trimmed_name,
            image_url=str_url,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )

        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        return _to_image_record(new_image)

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating image record: {str(db_err)}"
        )


@router.get("/", response_model=List[ImageRecord], status_code=status.HTTP_200_OK)
def list_images(
    category: Optional[str] = Query(None, description="Filter by category folder (e.g., ImageA, ImageB)"),
    aircraft_model: Optional[str] = Query(None, description="Filter by aircraft model name (partial or exact)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Optional maximum number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all registered image records from PostgreSQL (sales_hj.aircraft_images).
    Supports optional filtering by category or aircraft model and pagination.
    Returns an empty list [] if no records match.
    """
    try:
        query = db.query(AircraftImage).filter(AircraftImage.is_active == True)

        if category:
            query = query.filter(func.lower(AircraftImage.category) == category.strip().lower())

        if aircraft_model:
            search_pattern = f"%{aircraft_model.strip().lower()}%"
            query = query.filter(func.lower(AircraftImage.aircraft_model).like(search_pattern))

        query = query.order_by(AircraftImage.created_at.asc(), AircraftImage.image_name.asc()).offset(skip)

        if limit:
            query = query.limit(limit)

        records = query.all()

        return [_to_image_record(r) for r in records]
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while retrieving images: {str(db_err)}"
        )


@router.get("/{image_id}", response_model=ImageRecord, status_code=status.HTTP_200_OK)
def get_image(image_id: str, db: Session = Depends(get_db)):
    """
    Fetch a specific image record by its unique identifier (e.g., IMG-001) from PostgreSQL.
    Returns 404 Not Found if the image does not exist.
    """
    try:
        record = db.query(AircraftImage).filter(
            AircraftImage.image_id == image_id,
            AircraftImage.is_active == True
        ).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID '{image_id}' not found"
            )

        return _to_image_record(record)
    except HTTPException:
        raise
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching image: {str(db_err)}"
        )


@router.delete("/{image_id}", response_model=ImageRecord, status_code=status.HTTP_200_OK)
def delete_image(image_id: str, db: Session = Depends(get_db)):
    """
    Remove an image record from PostgreSQL (sales_hj.aircraft_images).
    NOTE: In accordance with data retention requirements, this removes or disables
    the database record only. It NEVER modifies, overwrites, or deletes files in Cloudflare R2.
    """
    try:
        record = db.query(AircraftImage).filter(
            AircraftImage.image_id == image_id,
            AircraftImage.is_active == True
        ).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID '{image_id}' not found"
            )

        # Snapshot of record before deletion for response
        response_data = _to_image_record(record)

        # Remove from PostgreSQL (never touch R2)
        db.delete(record)
        db.commit()

        return response_data
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while deleting image record: {str(db_err)}"
        )
