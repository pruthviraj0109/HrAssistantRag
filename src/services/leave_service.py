"""
Business logic for leave operations. Kept separate from the LLM tool layer
so validation/security rules are enforced regardless of what the LLM decides
to call (Security Requirement: "The LLM must never be the only security layer").
"""

from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from db.models import Employee, LeaveBalance, LeaveRequest

VALID_LEAVE_TYPES = {"sick", "casual", "earned"}


class LeaveServiceError(Exception):
    """Raised for any validation failure — caught and converted to a clean message by the tool layer."""


def get_employee_for_user(db: Session, user_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    if not employee:
        raise LeaveServiceError("No employee record found for this account.")
    return employee


def check_leave_balance(
    db: Session, user_id: int, leave_type: Optional[str] = None
) -> list[dict]:
    employee = get_employee_for_user(db, user_id)
    query = db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee.id)
    if leave_type:
        if leave_type.lower() not in VALID_LEAVE_TYPES:
            raise LeaveServiceError(
                f"Invalid leave type '{leave_type}'. Valid types: {VALID_LEAVE_TYPES}"
            )
        query = query.filter(LeaveBalance.leave_type == leave_type.lower())

    balances = query.all()
    if not balances:
        raise LeaveServiceError("No leave balance records found.")

    return [
        {
            "leave_type": b.leave_type,
            "total_days": b.total_days,
            "used_days": b.used_days,
            "remaining_days": b.remaining_days,
        }
        for b in balances
    ]


def validate_leave_request(
    db: Session, user_id: int, leave_type: str, start_date: date, end_date: date
) -> dict:
    """Validates without writing to the DB — used to show a confirmation summary first."""
    employee = get_employee_for_user(db, user_id)

    if leave_type.lower() not in VALID_LEAVE_TYPES:
        raise LeaveServiceError(
            f"Invalid leave type '{leave_type}'. Valid types: {VALID_LEAVE_TYPES}"
        )

    if start_date > end_date:
        raise LeaveServiceError("Start date cannot be after end date.")

    requested_days = (end_date - start_date).days + 1

    balance = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.leave_type == leave_type.lower(),
        )
        .first()
    )
    if not balance:
        raise LeaveServiceError(
            f"No '{leave_type}' leave balance found for this employee."
        )

    if requested_days > balance.remaining_days:
        raise LeaveServiceError(
            f"Insufficient balance: requested {requested_days} days, only {balance.remaining_days} remaining."
        )

    return {
        "employee_id": employee.id,
        "leave_type": leave_type.lower(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "requested_days": requested_days,
        "remaining_after": balance.remaining_days - requested_days,
    }


def submit_leave_request(
    db: Session,
    user_id: int,
    leave_type: str,
    start_date: date,
    end_date: date,
    reason: Optional[str] = None,
) -> dict:
    """Actually writes to the DB. Only call this AFTER validate_leave_request + explicit user confirmation."""
    validated = validate_leave_request(db, user_id, leave_type, start_date, end_date)
    employee = get_employee_for_user(db, user_id)

    leave_request = LeaveRequest(
        employee_id=employee.id,
        leave_type=leave_type.lower(),
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status="pending",
    )
    db.add(leave_request)

    balance = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.leave_type == leave_type.lower(),
        )
        .first()
    )
    balance.used_days += validated["requested_days"]

    db.commit()
    db.refresh(leave_request)

    return {"request_id": leave_request.id, "status": leave_request.status, **validated}


def check_leave_status(
    db: Session, user_id: int, request_id: Optional[int] = None
) -> list[dict]:
    employee = get_employee_for_user(db, user_id)
    query = db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee.id)
    if request_id:
        query = query.filter(LeaveRequest.id == request_id)

    requests = query.order_by(LeaveRequest.created_at.desc()).all()
    if not requests:
        raise LeaveServiceError("No leave requests found.")

    return [
        {
            "request_id": r.id,
            "leave_type": r.leave_type,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "status": r.status,
        }
        for r in requests
    ]


def cancel_leave_request(db: Session, user_id: int, request_id: int) -> dict:
    employee = get_employee_for_user(db, user_id)
    leave_request = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.id == request_id, LeaveRequest.employee_id == employee.id)
        .first()
    )
    if not leave_request:
        raise LeaveServiceError(
            "Leave request not found or does not belong to this employee."
        )
    if leave_request.status not in ("pending", "approved"):
        raise LeaveServiceError(
            f"Cannot cancel a request with status '{leave_request.status}'."
        )

    balance = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.leave_type == leave_request.leave_type,
        )
        .first()
    )
    requested_days = (leave_request.end_date - leave_request.start_date).days + 1
    if balance:
        balance.used_days = max(0, balance.used_days - requested_days)

    leave_request.status = "cancelled"
    db.commit()

    return {"request_id": leave_request.id, "status": "cancelled"}
