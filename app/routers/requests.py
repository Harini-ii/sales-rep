
from datetime import datetime, timezone
from uuid import UUID
from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.request import (
    AviationRequestModel,
    SalesRequestHJ,
    RequestStatusHistoryModel,
)
from app.schemas.request import (
    SalesRequestCreate,
    SalesRequestUpdate,
    SalesRequestResponse,
    SalesRequestStatusUpdate,
    LegacyAviationRequestResponse,
    RequestStatus,
)

router = APIRouter(prefix="/requests", tags=["Requests"])


def _find_request(db: Session, request_key: str) -> SalesRequestHJ | None:
    """Find a request by its UUID primary key or public request number."""
    try:
        request_uuid = UUID(request_key)
    except ValueError:
        request_uuid = None

    if request_uuid is not None:
        record = db.query(SalesRequestHJ).filter(SalesRequestHJ.id == request_uuid).first()
        if record:
            return record

    return (
        db.query(SalesRequestHJ)
        .filter(SalesRequestHJ.request_number == request_key)
        .first()
    )


def _request_response(db: Session, record: SalesRequestHJ) -> SalesRequestResponse:
    latest_status = (
        db.query(RequestStatusHistoryModel.new_status)
        .filter(RequestStatusHistoryModel.request_id == str(record.request_number))
        .order_by(RequestStatusHistoryModel.changed_at.desc())
        .limit(1)
        .scalar()
    )
    response = SalesRequestResponse.model_validate(record)
    return response.model_copy(update={"status": latest_status})


def _legacy_request_response(
    record: AviationRequestModel,
) -> LegacyAviationRequestResponse:
    customer_name = record.customer_name
    customer_email = record.customer_email
    if not customer_name and isinstance(record.customer_details, dict):
        customer_name = record.customer_details.get("name")
    if not customer_email and isinstance(record.customer_details, dict):
        customer_email = record.customer_details.get("email")

    raw_status = record.status or "DRAFT"
    if raw_status not in RequestStatus._value2member_map_:
        raw_status = "DRAFT"

    return LegacyAviationRequestResponse(
        request_id=record.request_id,
        customer_id=record.customer_id,
        request_type=record.request_type or "BOOKING",
        email=customer_email or record.customer_id,
        mobile=record.customer_mobile,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_mobile=record.customer_mobile,
        status=raw_status,
        service=record.service or "AVIATION",
        passengers=record.passengers or 1,
        event_flight_details=record.event_flight_details or {},
        customer_details=record.customer_details or {
            "name": customer_name,
            "email": customer_email,
        },
    )


@router.get("/", response_model=List[SalesRequestResponse])
def get_all_requests(db: Session = Depends(get_db)):
    try:
        records = (
            db.query(SalesRequestHJ)
            .order_by(SalesRequestHJ.created_at.desc())
            .all()
        )
        return [_request_response(db, record) for record in records]
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error retrieving requests",
        )


@router.get(
    "/{request_id}",
    response_model=Union[SalesRequestResponse, LegacyAviationRequestResponse],
)
def get_request(request_id: str, db: Session = Depends(get_db)):
    try:
        record = _find_request(db, request_id.strip())
        if record:
            return _request_response(db, record)

        legacy_record = (
            db.query(AviationRequestModel)
            .filter(AviationRequestModel.request_id.ilike(request_id.strip()))
            .first()
        )
        if legacy_record:
            return _legacy_request_response(legacy_record)

        raise HTTPException(
            status_code=404,
            detail=f"Request '{request_id}' not found",
        )

    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error fetching request",
        )


@router.put(
    "/{request_id}/status",
    response_model=SalesRequestResponse,
)
def update_request_status(
    request_id: str,
    update_data: SalesRequestStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        record = _find_request(db, request_id.strip())

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Request '{request_id}' not found",
            )

        old_status = (
            db.query(RequestStatusHistoryModel.new_status)
            .filter(RequestStatusHistoryModel.request_id == str(record.request_number))
            .order_by(RequestStatusHistoryModel.changed_at.desc())
            .limit(1)
            .scalar()
        )
        new_status = update_data.status.value
        record.updated_at = datetime.now(timezone.utc)

        history_entry = RequestStatusHistoryModel(
            request_id=str(record.request_number),
            old_status=old_status,
            new_status=new_status,
            changed_by="sales_team",
        )

        db.add(history_entry)
        db.commit()
        db.refresh(record)

        return _request_response(db, record)

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error updating request status",
        )


@router.post(
    "/",
    response_model=SalesRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    data: SalesRequestCreate,
    db: Session = Depends(get_db),
):
    try:
        new_record = SalesRequestHJ(
            **data.model_dump(),
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return new_record

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error creating request",
        )
