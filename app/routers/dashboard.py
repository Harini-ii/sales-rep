from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", status_code=status.HTTP_200_OK)
@router.get("/sales/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Retrieve sales dashboard summary metrics for overview cards:
    - Open Requests
    - Active Subscriptions
    - Credits Held by Customers
    - Customers with Access
    Supports both snake_case and camelCase keys for seamless frontend compatibility.
    """
    open_requests = db.execute(
        text('SELECT count(*) FROM sales_hj."SALES_REQUESTS_HJ";')
    ).scalar() or 0

    customers_with_access = db.execute(
        text('SELECT count(*) FROM sales_hj."CUSTOMERS_HJ";')
    ).scalar() or 0

    credits_held = db.execute(
        text('SELECT COALESCE(sum(credits), 0) FROM sales_hj."CUSTOMERS_HJ";')
    ).scalar() or 0

    active_subscriptions = db.execute(
        text("""
            SELECT count(*) FROM sales_hj."CUSTOMERS_HJ" 
            WHERE subscription IS NOT NULL AND subscription != '' AND LOWER(subscription) != 'none';
        """)
    ).scalar() or 0

    return {
        # snake_case
        "open_requests": open_requests,
        "active_subscriptions": active_subscriptions,
        "credits_held": credits_held,
        "customers_with_access": customers_with_access,
        # camelCase
        "openRequests": open_requests,
        "activeSubscriptions": active_subscriptions,
        "creditsHeld": credits_held,
        "customersWithAccess": customers_with_access,
    }
