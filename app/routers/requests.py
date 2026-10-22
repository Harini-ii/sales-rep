from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.request import (
    AviationRequest,
    AviationRequestCreate,
    AviationRequestUpdate,
    AviationRequestStatusResponse,
    RequestStatus
)
from app.models.request import AviationRequestModel, RequestStatusHistoryModel
from app.database import get_db
from app.data import mock_data

router = APIRouter(
    prefix="/requests",
    tags=["Requests"]
)


def _to_aviation_response(rec: AviationRequestModel) -> AviationRequest:
    """Helper to convert database AviationRequestModel to AviationRequest schema."""
    customer_name = rec.customer_name
    customer_email = rec.customer_email
    if not customer_name and isinstance(rec.customer_details, dict):
        customer_name = rec.customer_details.get("name")
    if not customer_email and isinstance(rec.customer_details, dict):
        customer_email = rec.customer_details.get("email")

    return AviationRequest(
        request_id=rec.request_id,
        customer_id=rec.customer_id,
        request_type=rec.request_type or "BOOKING",
        email=rec.customer_email or rec.customer_id,
        mobile=rec.customer_mobile,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_mobile=rec.customer_mobile,
        status=RequestStatus(rec.status) if rec.status in RequestStatus._value2member_map_ else RequestStatus.DRAFT,
        service=rec.service,
        passengers=rec.passengers or 1,
        event_flight_details=rec.event_flight_details or {},
        customer_details=rec.customer_details or {"name": customer_name, "email": customer_email}
    )


@router.get("/", response_model=List[AviationRequest], status_code=status.HTTP_200_OK)
def get_all_requests(db: Session = Depends(get_db)):
    """
    Retrieve all aviation and booking requests for the Sales Requests dashboard list.
    """
    try:
        records = db.query(AviationRequestModel).order_by(AviationRequestModel.request_id.desc()).all()
        return [_to_aviation_response(r) for r in records]
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving requests: {str(db_err)}"
        )


@router.get("/{request_id}", response_model=AviationRequest, status_code=status.HTTP_200_OK)
def get_request(request_id: str, db: Session = Depends(get_db)):
    """
    Fetch full aviation request details by request ID (used when clicking 'VIEW').
    """
    clean_id = request_id.strip()
    try:
        record = db.query(AviationRequestModel).filter(AviationRequestModel.request_id.ilike(clean_id)).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Request '{request_id}' not found"
            )
        return _to_aviation_response(record)
    except HTTPException:
        raise
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error fetching request: {str(db_err)}"
        )


@router.put("/{request_id}/status", response_model=AviationRequestStatusResponse, status_code=status.HTTP_200_OK)
@router.post("/{request_id}/status", response_model=AviationRequestStatusResponse, status_code=status.HTTP_200_OK)
def update_request_status(request_id: str, update_data: AviationRequestUpdate, db: Session = Depends(get_db)):
    """
    Update the status of an aviation request via the dropdown.
    Logs the status transition into sales_hj.request_status_history and commits to PostgreSQL.
    """
    clean_id = request_id.strip()
    try:
        record = db.query(AviationRequestModel).filter(AviationRequestModel.request_id.ilike(clean_id)).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Request '{request_id}' not found"
            )

        old_status = record.status
        new_status = update_data.status.value

        # Update status
        record.status = new_status
        record.updated_at = datetime.now(timezone.utc)

        # Log status transition history
        current_user = mock_data.profile_db.get("email") or "sales_team"
        history_entry = RequestStatusHistoryModel(
            request_id=record.request_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user
        )
        db.add(history_entry)

        db.commit()
        db.refresh(record)

        return AviationRequestStatusResponse(
            request_id=record.request_id,
            status=update_data.status,
            message="Request status updated successfully"
        )
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error updating request status: {str(db_err)}"
        )


@router.post("/", response_model=AviationRequest, status_code=status.HTTP_201_CREATED)
def create_request(data: AviationRequestCreate, db: Session = Depends(get_db)):
    """
    Create a new aviation request record in sales_hj.requests.
    """
    req_id = data.request_id
    if not req_id:
        count = db.query(AviationRequestModel).count() + 1
        req_id = f"HJ-{1020 + count:05d}"

    existing = db.query(AviationRequestModel).filter(AviationRequestModel.request_id == req_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request with ID '{req_id}' already exists."
        )

    flight_details = data.event_flight_details.model_dump() if data.event_flight_details else {}
    cust_details = data.customer_details.model_dump() if data.customer_details else {
        "name": data.customer_name,
        "email": data.customer_email
    }

    new_rec = AviationRequestModel(
        request_id=req_id,
        customer_id=data.customer_id,
        request_type=data.request_type or "BOOKING",
        service=data.service or "AVIATION",
        status=data.status.value if data.status else "DRAFT",
        passengers=data.passengers or 1,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        customer_mobile=data.customer_mobile,
        event_flight_details=flight_details,
        customer_details=cust_details
    )

    try:
        db.add(new_rec)
        db.commit()
        db.refresh(new_rec)
        return _to_aviation_response(new_rec)
    except SQLAlchemyError as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating request: {str(db_err)}"
        )

