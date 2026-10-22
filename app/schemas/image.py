from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field, field_validator


class ImageCreate(BaseModel):
    """
    Schema for creating/registering a new image record.
    """
    image_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Descriptive name of the image",
        examples=["Helite Jet Falcon 8X Exterior"]
    )
    image_url: HttpUrl = Field(
        ...,
        description="A valid HTTP or HTTPS URL pointing to the image",
        examples=["https://images.unsplash.com/photo-1540959733332-eab4deabeeaf"]
    )

    @field_validator("image_name")
    @classmethod
    def validate_image_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Image name cannot be empty or whitespace only")
        return trimmed


class ImageRecord(BaseModel):
    """
    Schema for an image record representation.
    Explicitly indicates temporary in-memory status and lack of permanent DB persistence.
    """
    image_id: str = Field(
        ...,
        description="Unique identifier for the image record (e.g., IMG-001)",
        examples=["IMG-001"]
    )
    image_name: str = Field(
        ...,
        description="Descriptive name of the image",
        examples=["Helite Jet Falcon 8X Exterior"]
    )
    image_url: str = Field(
        ...,
        description="URL pointing to the image",
        examples=["https://images.unsplash.com/photo-1540959733332-eab4deabeeaf"]
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the image record was created"
    )
    storage_type: str = Field(
        default="in_memory_temporary",
        description="Current storage mechanism (in-memory temporary)"
    )
    is_persisted_to_db: bool = Field(
        default=False,
        description="Flag indicating if the record is persisted to a permanent database"
    )
    category: Optional[str] = Field(
        default=None,
        description="Category classification folder (e.g., ImageA, ImageB)"
    )
    aircraft_model: Optional[str] = Field(
        default=None,
        description="Aircraft model name"
    )
    file_format: Optional[str] = Field(
        default=None,
        description="File format extension (e.g., jpg, png, webp)"
    )
    # r2_key: Optional[str] = Field(
    #     default=None,
    #     description="Cloudflare R2 storage key"
    # )
    note: str = Field(
        default="Persisted in PostgreSQL database (sales_hj.AIRCRAFT_IMAGES_HJ).",
        description="Advisory notice regarding persistence"
    )


class R2StatusResponse(BaseModel):
    """
    Status response for Cloudflare R2 bucket configuration.
    Never exposes credentials or secrets.
    """
    configured: bool
    bucket_name: str
    endpoint_url: str
    has_access_key: bool
    has_secret_key: bool
    has_public_domain: bool
    missing_configurations: List[str]
    notes: str
