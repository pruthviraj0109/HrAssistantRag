from datetime import date
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.tools import StructuredTool

from src.services import onboarding_service
from src.services.onboarding_service import OnboardingServiceError


class NoInput(BaseModel):
    pass


class TaskNameInput(BaseModel):
    task_name: str = Field(
        ...,
        description="Name of the onboarding task, or part of it. "
        "For example 'PAN card' or 'IT setup'.",
    )


class CompleteTaskInput(BaseModel):
    task_name: str = Field(
        ..., description="Name of the onboarding task to mark as complete."
    )
    confirmed: bool = Field(
        ...,
        description="Must be True. Only set True after the user has explicitly "
        "confirmed they want this task marked complete.",
    )


class CompleteTrainingInput(BaseModel):
    course_name: str = Field(..., description="Name of the training course.")
    confirmed: bool = Field(
        ...,
        description="Must be True. Only set True after explicit user confirmation.",
    )


def build_onboarding_tools(db: Session, user_id: int) -> list[StructuredTool]:
    """
    Onboarding and training tools bound to one authenticated user's session.
    user_id comes from the JWT-decoded current_user — never from LLM input.
    """

    # -------------------------------------------------- onboarding checklist
    def check_onboarding_status() -> str:
        try:
            data = onboarding_service.get_checklist(db, user_id)
        except OnboardingServiceError as e:
            return f"Error: {e}"

        if data["all_complete"]:
            return (
                f"All {data['total']} onboarding tasks are complete. "
                "Nothing outstanding."
            )

        lines = [
            f"{data['completed']} of {data['total']} onboarding tasks complete."
        ]

        if data["overdue"]:
            lines.append("")
            lines.append(f"OVERDUE ({len(data['overdue'])}):")
            for t in data["overdue"]:
                late = abs(t["days_left"]) if t["days_left"] is not None else None
                when = f" — {late} day(s) late" if late is not None else ""
                lines.append(f"- {t['task_name']}{when}")

        if data["pending"]:
            lines.append("")
            lines.append(f"PENDING ({len(data['pending'])}):")
            for t in data["pending"]:
                d = t["days_left"]
                if d is None:
                    when = ""
                elif d == 0:
                    when = " — due today"
                else:
                    when = f" — due in {d} day(s)"
                lines.append(f"- {t['task_name']}{when}")

        return "\n".join(lines)

    def mark_task_complete(task_name: str, confirmed: bool) -> str:
        if not confirmed:
            return (
                "Not marked. Ask the user to confirm they want "
                f"'{task_name}' marked as complete, then call this tool again."
            )
        try:
            r = onboarding_service.mark_task_complete(db, user_id, task_name)
        except OnboardingServiceError as e:
            return f"Could not update: {e}"

        if r["remaining"] == 0:
            return (
                f"'{r['task_name']}' marked complete. "
                "That was the last item — onboarding is finished."
            )
        return (
            f"'{r['task_name']}' marked complete on {r['completed_at']}. "
            f"{r['remaining']} task(s) remaining."
        )

    def get_task_guidance(task_name: str) -> str:
        try:
            r = onboarding_service.get_task_details(db, user_id, task_name)
        except OnboardingServiceError as e:
            return f"Error: {e}"

        bits = [f"Task: {r['task_name']}"]
        if r["category"]:
            bits.append(f"Category: {r['category']}")
        bits.append(f"Status: {r['status']}")
        if r["due_date"]:
            bits.append(f"Due: {r['due_date']}")
        if r["completed_at"]:
            bits.append(f"Completed: {r['completed_at']}")
        bits.append(
            "This tool returns the task's status only. For instructions on how to "
            "complete it, tell the user to check the onboarding policy documents."
        )
        return "\n".join(bits)

    # -------------------------------------------------------------- training
    def check_training_status() -> str:
        try:
            data = onboarding_service.get_training_status(db, user_id)
        except OnboardingServiceError as e:
            return f"Error: {e}"

        lines = []

        if data["outstanding"]:
            mand = data["mandatory_outstanding"]
            if mand:
                lines.append(f"MANDATORY TRAINING OUTSTANDING ({len(mand)}):")
                for r in mand:
                    lines.append(f"- {r['course_name']}")
            optional = [r for r in data["outstanding"] if not r["mandatory"]]
            if optional:
                lines.append("")
                lines.append(f"OPTIONAL, NOT STARTED ({len(optional)}):")
                for r in optional:
                    lines.append(f"- {r['course_name']}")
        else:
            lines.append(
                f"All {data['total']} training records are complete."
            )

        # expiries are the point of this tool — nobody tracks them manually
        if data["expiring"]:
            lines.append("")
            lines.append("EXPIRING OR EXPIRED:")
            for r in data["expiring"]:
                if r["expired"]:
                    lines.append(
                        f"- {r['course_name']} expired on {r['expires_at']} "
                        "and must be retaken."
                    )
                else:
                    lines.append(
                        f"- {r['course_name']} expires on {r['expires_at']} "
                        f"({r['days_left']} day(s) away)."
                    )

        return "\n".join(lines)

    def mark_training_complete(course_name: str, confirmed: bool) -> str:
        if not confirmed:
            return (
                "Not marked. Ask the user to confirm they have completed "
                f"'{course_name}', then call this tool again."
            )
        try:
            r = onboarding_service.mark_training_complete(db, user_id, course_name)
        except OnboardingServiceError as e:
            return f"Could not update: {e}"

        msg = f"'{r['course_name']}' marked complete on {r['completed_at']}."
        if r["expires_at"]:
            msg += f" It expires on {r['expires_at']}."
        return msg

    # ----------------------------------------------------------------- tools
    return [
        StructuredTool.from_function(
            func=check_onboarding_status,
            name="check_onboarding_status",
            description=(
                "Shows the authenticated employee's onboarding checklist: what is "
                "complete, pending and overdue. Use for 'what do I need to do', "
                "'what is pending', 'onboarding status' type questions."
            ),
            args_schema=NoInput,
        ),
        StructuredTool.from_function(
            func=mark_task_complete,
            name="mark_task_complete",
            description=(
                "Marks one onboarding task as complete. Only call with confirmed=True "
                "after the user has explicitly confirmed. This writes to the record."
            ),
            args_schema=CompleteTaskInput,
        ),
        StructuredTool.from_function(
            func=get_task_guidance,
            name="get_task_guidance",
            description=(
                "Returns the status and due date of a single onboarding task. Use when "
                "the user asks about one specific item on their checklist."
            ),
            args_schema=TaskNameInput,
        ),
        StructuredTool.from_function(
            func=check_training_status,
            name="check_training_status",
            description=(
                "Shows the employee's training records: mandatory courses outstanding, "
                "and any completed training that has expired or expires soon. Use for "
                "'what training do I need', 'am I up to date on compliance' questions."
            ),
            args_schema=NoInput,
        ),
        StructuredTool.from_function(
            func=mark_training_complete,
            name="mark_training_complete",
            description=(
                "Marks a training course as complete. Only call with confirmed=True "
                "after explicit user confirmation. This writes to the record."
            ),
            args_schema=CompleteTrainingInput,
        ),
    ]