from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.tools import StructuredTool
from src.services import leave_service
from src.services.leave_service import LeaveServiceError


class CheckBalanceInput(BaseModel):
    leave_type: Optional[str] = Field(
        default=None,
        description="Specific leave type to check (sick/causal/earned). Omit to see all types.",
    )


class ValidateLeaveInput(BaseModel):
    leave_type: str = Field(..., description="Type of leave: sick, casual, or earned.")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format.")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format.")


class SubmitLeaveInput(BaseModel):
    leave_type: str = Field(..., description="Type of leave: sick, casual, or earned.")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format.")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format.")
    reason: Optional[str] = Field(
        default=None, description="Optional reason for the leave."
    )
    confirmed: bool = Field(
        ...,
        description="Must be True . Only set True if the user has explicitly confirmed after seeing a summary.",
    )


class LeaveStatusInput(BaseModel):
    request_id: Optional[int] = Field(
        default=None, description="Specific request ID to check. Omit to list all."
    )


class CancelLeaveInput(BaseModel):
    request_id: int = Field(..., description="The ID of the leave request to cancel.")


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def build_leave_tools(db: Session, user_id: int) -> list[StructuredTool]:
    """
    Builds all leave-related tools bound to one authenticated user's session.
    user_id comes from the JWT-decoded current_user — never from LLM input.
    """

    def check_leave_balance(leave_type: Optional[str] = None) -> str:
        try:
            balances = leave_service.check_leave_balance(db, user_id, leave_type)
        except LeaveServiceError as e:
            return f"Error: {e}"
        lines = [
            f"- {b['leave_type']}: {b['remaining_days']} of {b['total_days']} days remaining"
            for b in balances
        ]

        return "\n".join(lines)

    def validate_leave(leave_type: str, start_date: str, end_date: str) -> str:
        try:
            result = leave_service.validate_leave_request(
                db, user_id, leave_type, _parse_date(start_date), _parse_date(end_date)
            )
        except (LeaveServiceError, ValueError) as e:
            return f"Cannot proceed: {e}"

        return (
            f"Confirm: {result['requested_days']} day(s) of {result['leave_type']} leave "
            f"from {result['start_date']} to {result['end_date']}. "
            f"Remaining balance after approval: {result['remaining_after']} days. "
            f"Ask the user to explicitly confirm before calling submit_leave_request."
        )

    def submit_leave_request(
        leave_type: str,
        start_date: str,
        end_date: str,
        confirmed: bool,
        reason: Optional[str] = None,
    ) -> str:

        if not confirmed:
            return "Not submitted - user confirmation is required first. Call validate_leave to show a summary."
        try:
            result = leave_service.submit_leave_request(
                db,
                user_id,
                leave_type,
                _parse_date(start_date),
                _parse_date(end_date),
                reason,
            )

        except (LeaveServiceError, ValueError) as e:
            return f"Submission failed: {e}"
        return f"Leave request #{result['request_id']} submitted successfully. Status:{result['status']}."

    def check_leave_status(request_id: Optional[int] = None) -> str:
        try:
            requests = leave_service.check_leave_status(db, user_id, request_id)
        except LeaveServiceError as e:
            return f"Error: {e}"

        lines = [
            f"- #{r['request_id']}: {r['leave_type']} leave, {r['start_date']} to {r['end_date']}, status: {r['status']}"
            for r in requests
        ]
        return "\n".join(lines)

    def cancel_leave_request(request_id: int) -> str:
        try:
            result = leave_service.cancel_leave_request(db, user_id, request_id)
        except LeaveServiceError as e:
            return f"Cannot cancel: {e}"
        return f"Leave request #{result['request_id']} cancelled."

    return [
        StructuredTool.from_function(
            func=check_leave_balance,
            name="check_leave_balance",
            description="Check the authenticated employee's leave balance. Use for 'how many leaves do I have' type questions.",
            args_schema=CheckBalanceInput,
        ),
        StructuredTool.from_function(
            func=validate_leave,
            name="validate_leave",
            description="Validates a leave request and shows a confirmation summary WITHOUT submitting it. Always call this before submit_leave_request.",
            args_schema=ValidateLeaveInput,
        ),
        StructuredTool.from_function(
            func=submit_leave_request,
            name="submit_leave_request",
            description="Submits a leave request. Only call with confirmed=True after the user has explicitly confirmed a validate_leave summary.",
            args_schema=SubmitLeaveInput,
        ),
        StructuredTool.from_function(
            func=check_leave_status,
            name="check_leave_status",
            description="Checks the status of the employee's leave request(s).",
            args_schema=LeaveStatusInput,
        ),
        StructuredTool.from_function(
            func=cancel_leave_request,
            name="cancel_leave_request",
            description="Cancels a pending or approved leave request belonging to the employee.",
            args_schema=CancelLeaveInput,
        ),
    ]
