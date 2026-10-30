import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.event import SalesEventHJ
from app.schemas.event import (
    SalesEventResponse,
    SalesEventStatusUpdate,
    SalesEventCreate,
    SalesEventUpdate,
)

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=List[SalesEventResponse], status_code=status.HTTP_200_OK)
def get_all_events(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter events by status"),
    customer_id: Optional[UUID] = Query(None, description="Filter events by customer UUID"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Maximum records to return"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all sales events from sales_hj.SALES_EVENTS_HJ with optional filtering.
    """
    try:
        query = db.query(SalesEventHJ).order_by(SalesEventHJ.created_at.desc())
        if status_filter:
            query = query.filter(SalesEventHJ.status.ilike(status_filter.strip()))
        if customer_id:
            query = query.filter(SalesEventHJ.customer_id == customer_id)
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        records = query.all()
        return records
    except SQLAlchemyError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving events: {str(err)}",
        )


@router.get("/{event_id}", response_model=SalesEventResponse, status_code=status.HTTP_200_OK)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a single sales event by its UUID.
    """
    clean_id = event_id.strip()
    try:
        ev_uuid = UUID(clean_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event UUID format: '{event_id}'",
        )

    try:
        record = db.query(SalesEventHJ).filter(SalesEventHJ.event_id == ev_uuid).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event '{event_id}' not found",
            )
        return record
    except HTTPException:
        raise
    except SQLAlchemyError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving event: {str(err)}",
        )


@router.put("/{event_id}/status", response_model=SalesEventResponse, status_code=status.HTTP_200_OK)
def update_event_status(
    event_id: str,
    update_data: SalesEventStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Update the status of a sales event.
    """
    clean_id = event_id.strip()
    try:
        ev_uuid = UUID(clean_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event UUID format: '{event_id}'",
        )

    try:
        record = db.query(SalesEventHJ).filter(SalesEventHJ.event_id == ev_uuid).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event '{event_id}' not found",
            )

        record.status = update_data.status
        db.commit()
        db.refresh(record)
        return record
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error updating event status: {str(err)}",
        )


@router.put("/{event_id}", response_model=SalesEventResponse, status_code=status.HTTP_200_OK)
def update_event(
    event_id: str,
    update_data: SalesEventUpdate,
    db: Session = Depends(get_db),
):
    """
    Update details of a sales event.
    """
    clean_id = event_id.strip()
    try:
        ev_uuid = UUID(clean_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event UUID format: '{event_id}'",
        )

    try:
        record = db.query(SalesEventHJ).filter(SalesEventHJ.event_id == ev_uuid).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event '{event_id}' not found",
            )

        for key, val in update_data.model_dump(exclude_unset=True).items():
            setattr(record, key, val)

        db.commit()
        db.refresh(record)
        return record
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error updating event: {str(err)}",
        )


@router.post("/", response_model=SalesEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: SalesEventCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new sales event record directly in sales_hj.SALES_EVENTS_HJ.
    """
    try:
        new_record = SalesEventHJ(**event_data.model_dump())
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record
    except SQLAlchemyError as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating event: {str(err)}",
        )


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    """
    Delete a sales event by UUID.
    """
    clean_id = event_id.strip()
    try:
        ev_uuid = UUID(clean_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event UUID format: '{event_id}'",
        )

    try:
        record = db.query(SalesEventHJ).filter(SalesEventHJ.event_id == ev_uuid).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event '{event_id}' not found",
            )

        db.delete(record)
        db.commit()
        return {"message": f"Event '{event_id}' deleted successfully"}
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error deleting event: {str(err)}",
        )
