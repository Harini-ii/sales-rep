from datetime import date, datetime, timezone
import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.customer import Customer, CustomerCreate
from app.models.customer import CustomerModel
from app.database import get_db

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


def _to_customer_response(rec: CustomerModel) -> Customer:
    """Helper to convert sales_hj.CUSTOMERS_HJ to Customer schema."""
    cid_str = str(rec.customer_id) if rec.customer_id else str(rec.id)
    phone = rec.mobile or ""
    joined_date = rec.joined or (rec.created_at.date() if rec.created_at else date.today())
    return Customer(
        customer_id=cid_str,
        id=cid_str,
        name=rec.name,
        email=rec.email,
        phone_number=phone,
        mobile=phone,
        company=rec.company or "",
        country=rec.country or "",
        role="CUSTOMER",
        subscription=rec.subscription or "Basic",
        credits=rec.credits or 0,
        purchases=rec.purchases or 0,
        joined=joined_date,
        created_at=rec.created_at
    )


@router.get("/", response_model=List[Customer], status_code=status.HTTP_200_OK)
def get_all_customers(db: Session = Depends(get_db)):
    """
    Retrieve all customer records from sales_hj.CUSTOMERS_HJ table.
    """
    try:
        customers = db.query(CustomerModel).order_by(CustomerModel.id.asc()).all()
        return [_to_customer_response(c) for c in customers]
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving customers from sales_hj: {str(db_err)}"
        )


@router.get("/{customer_id}", response_model=Customer, status_code=status.HTTP_200_OK)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """
    Fetch customer details by customer UUID or ID from sales_hj.CUSTOMERS_HJ table.
    """
    try:
        customer = None
        # 1. Check by UUID string
        try:
            val_uuid = uuid.UUID(str(customer_id).strip())
            customer = db.query(CustomerModel).filter(CustomerModel.customer_id == val_uuid).first()
        except ValueError:
            pass

        # 2. Check by integer ID if not found
        if not customer:
            try:
                val_int = int(str(customer_id).strip())
                customer = db.query(CustomerModel).filter(CustomerModel.id == val_int).first()
            except ValueError:
                pass

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Customer with ID '{customer_id}' not found in sales_hj.CUSTOMERS_HJ"
            )
        return _to_customer_response(customer)
    except HTTPException:
        raise
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error fetching customer: {str(db_err)}"
        )


@router.post("/", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    """
    Create a new customer record directly in sales_hj.CUSTOMERS_HJ table.
    """
    target_email = str(customer_data.email).strip().lower()
    existing = db.query(CustomerModel).filter(CustomerModel.email == target_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with email '{target_email}' already exists in sales_hj.CUSTOMERS_HJ."
        )

    phone = customer_data.mobile or customer_data.phone_number or ""
    new_customer = CustomerModel(
        customer_id=uuid.uuid4(),
        name=customer_data.name.strip(),
        email=target_email,
        mobile=phone.strip(),
        country=customer_data.country or "",
        company=customer_data.company or "",
        subscription=customer_data.subscription or "Basic",
        credits=customer_data.credits if customer_data.credits is not None else 0,
        purchases=customer_data.purchases if customer_data.purchases is not None else 0,
        joined=customer_data.joined or date.today(),
        created_at=datetime.now(timezone.utc)
    )

    try:
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        return _to_customer_response(new_customer)
    except SQLAlchemyError as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating customer: {str(db_err)}"
        )


