from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.profile import AccountUpdate, PasswordUpdate
from app.models.sales_team import SalesTeamMember, PasswordChange, PersonalInformation
from app.database import get_db
from app.services.security import hash_password, verify_password
import app.data.mock_data as mock_data

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)


def _get_current_salesperson(db: Session) -> SalesTeamMember:
    """
    Resolves the current salesperson record from admin_hj.sales_team_hj
    based on the backend profile session context.
    Does NOT trust client-supplied identity parameters.
    """
    current_email = (mock_data.profile_db.get("email") or "abhi@gmail.com").strip()
    member = db.query(SalesTeamMember).filter(SalesTeamMember.email == current_email).first()

    if not member:
        existing_first = db.query(SalesTeamMember).first()
        if existing_first:
            member = existing_first
        else:
            member = SalesTeamMember(
                full_name=mock_data.profile_db.get("full_name") or "Salesperson",
                email=current_email,
                mobile_number=mock_data.profile_db.get("mobile") or "1234567890",
                password_hash=hash_password(mock_data.profile_db.get("password") or "oldpassword"),
                department="sales"
            )
            db.add(member)
            db.commit()
            db.refresh(member)

    return member


@router.patch("/account")
def update_account_details(account_data: AccountUpdate, db: Session = Depends(get_db)):
    """
    Update the current salesperson's personal and account details.
    Persists changes to the Admin sales team record (admin_hj.sales_team_hj)
    and logs updates to sales_hj.personal_information.
    """
    try:
        member = _get_current_salesperson(db)
        target_email = str(account_data.email).strip()

        # Check for duplicate email across other sales team members
        duplicate = (
            db.query(SalesTeamMember)
            .filter(
                SalesTeamMember.email == target_email,
                SalesTeamMember.id != member.id
            )
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email address '{target_email}' is already in use by another salesperson."
            )

        # Update primary salesperson record in admin_hj.sales_team_hj
        member.full_name = account_data.full_name.strip()
        member.email = target_email
        member.mobile_number = account_data.mobile.strip()

        # Update or log in sales_hj.personal_information
        personal_info = db.query(PersonalInformation).filter(PersonalInformation.sales_team_id == member.id).first()
        if not personal_info:
            personal_info = db.query(PersonalInformation).filter(PersonalInformation.email == member.email).first()

        if personal_info:
            personal_info.sales_team_id = member.id
            personal_info.full_name = member.full_name
            personal_info.email = member.email
            personal_info.mobile_number = member.mobile_number
            personal_info.updated_at = datetime.now()
        else:
            personal_info = PersonalInformation(
                sales_team_id=member.id,
                full_name=member.full_name,
                email=member.email,
                mobile_number=member.mobile_number,
                department=member.department
            )
            db.add(personal_info)

        db.commit()
        db.refresh(member)

        # Synchronize backend memory context
        mock_data.profile_db["full_name"] = member.full_name
        mock_data.profile_db["email"] = member.email
        mock_data.profile_db["mobile"] = member.mobile_number

        return {
            "message": "Account details updated successfully",
            "profile": {
                "full_name": member.full_name,
                "email": member.email,
                "mobile": member.mobile_number
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error updating profile: {str(db_err)}"
        )


@router.patch("/password")
def change_password(password_data: PasswordUpdate, db: Session = Depends(get_db)):
    """
    Change the current salesperson's password.
    Verifies the current password, validates match, and saves the new password
    hashed with PBKDF2-SHA256 in admin_hj.sales_team_hj and logs into sales_hj.password_changes.
    Never exposes passwords in responses or logs.
    """
    # 1. Check that new password and confirm password match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match"
        )

    try:
        member = _get_current_salesperson(db)

        # 2. Verify current password
        if not verify_password(password_data.current_password, member.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect current password"
            )

        # 3. Store new password securely hashed (never plaintext)
        member.password_hash = hash_password(password_data.new_password)

        # 4. Log the password change in sales_hj.password_changes
        change_log = PasswordChange(
            sales_team_id=member.id,
            email=member.email,
            password_hash=member.password_hash
        )
        db.add(change_log)

        db.commit()
        db.refresh(member)

        # Synchronize backend memory context
        mock_data.profile_db["password"] = password_data.new_password

        return {
            "message": "Password updated successfully"
        }
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error updating password: {str(db_err)}"
        )
