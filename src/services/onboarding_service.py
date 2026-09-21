from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from db.models import Employee, OnboardingTask, TrainingRecord


class OnboardingServiceError(Exception):
    """Raised for anything the caller should show the user as a plain message."""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

# The model writes typographic dashes — U+2011 non-breaking hyphen in
# "Anti‑Harassment", en and em dashes elsewhere. ilike is a literal substring
# match, so those never find a plain "-" in the database. Every incoming name
# is flattened before it is used in a query.
_DASHES = ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212")


def _normalise(text: str) -> str:
    if not text:
        return ""
    for ch in _DASHES:
        text = text.replace(ch, "-")
    return " ".join(text.split()).strip()


def _get_employee(db: Session, user_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    if not employee:
        raise OnboardingServiceError(
            "No employee record is linked to this account. HR needs to set one up."
        )
    return employee


def _due_date(employee: Employee, due_day: Optional[int]) -> Optional[date]:
    """Due dates are stored as 'days from joining' and resolved at read time,
    so a task never goes stale in the database."""
    joining = getattr(employee, "joining_date", None)
    if joining is None or due_day is None:
        return None
    return joining + timedelta(days=due_day)


def _match(records: list, field: str, needle: str) -> list:
    """Substring match in Python rather than SQL, so normalisation applies to
    both sides and the fallbacks below can be tried in order."""
    needle = _normalise(needle).lower()
    return [r for r in records if needle in _normalise(getattr(r, field)).lower()]


def _resolve_one(records: list, field: str, needle: str, kind: str):
    """Find exactly one record. Ambiguity is an error, not a coin flip —
    'submit' matches three tasks, and silently picking one would update the
    wrong row."""
    names = [getattr(r, field) for r in records]

    found = _match(records, field, needle)

    # fall back to the first word: "Anti" still finds "Anti-Harassment"
    # whatever punctuation the model used
    if not found:
        first = _normalise(needle).split()
        if first:
            found = _match(records, field, first[0])

    if not found:
        raise OnboardingServiceError(
            f"No {kind} matching '{needle}' was found. "
            f"Your {kind}s are: {', '.join(names)}."
        )

    if len(found) > 1:
        listed = ", ".join(f"'{getattr(r, field)}'" for r in found)
        raise OnboardingServiceError(
            f"'{needle}' matches more than one {kind}: {listed}. "
            "Ask the user which one they mean."
        )

    return found[0]


# ---------------------------------------------------------------------------
# onboarding checklist
# ---------------------------------------------------------------------------
def _all_tasks(db: Session, employee_id: int) -> list[OnboardingTask]:
    return (
        db.query(OnboardingTask)
        .filter(OnboardingTask.employee_id == employee_id)
        .order_by(OnboardingTask.id.asc())
        .all()
    )


def get_checklist(db: Session, user_id: int) -> dict:
    employee = _get_employee(db, user_id)

    tasks = _all_tasks(db, employee.id)
    if not tasks:
        raise OnboardingServiceError(
            "No onboarding checklist has been created for this employee yet."
        )

    # sorted here rather than in SQL, because due_day is nullable and NULLs
    # sort first in SQLite but last in Postgres
    tasks.sort(key=lambda t: (t.due_day is None, t.due_day or 0, t.id))

    today = date.today()
    overdue, pending, done = [], [], []

    for t in tasks:
        due = _due_date(employee, t.due_day)
        row = {
            "task_name": t.task_name,
            "category": t.category,
            "due_date": due.isoformat() if due else None,
            "days_left": (due - today).days if due else None,
            "status": t.status,
        }
        if t.status == "done":
            done.append(row)
        elif due is not None and due < today:
            overdue.append(row)
        else:
            pending.append(row)

    return {
        "total": len(tasks),
        "completed": len(done),
        "overdue": overdue,
        "pending": pending,
        "done": done,
        "all_complete": len(done) == len(tasks),
    }


def mark_task_complete(db: Session, user_id: int, task_name: str) -> dict:
    employee = _get_employee(db, user_id)

    tasks = _all_tasks(db, employee.id)
    if not tasks:
        raise OnboardingServiceError(
            "No onboarding checklist has been created for this employee yet."
        )

    task = _resolve_one(tasks, "task_name", task_name, "onboarding task")

    if task.status == "done":
        raise OnboardingServiceError(f"'{task.task_name}' is already marked complete.")

    task.status = "done"
    task.completed_at = date.today()
    db.commit()
    db.refresh(task)

    remaining = (
        db.query(OnboardingTask)
        .filter(
            OnboardingTask.employee_id == employee.id,
            OnboardingTask.status != "done",
        )
        .count()
    )

    return {
        "task_name": task.task_name,
        "completed_at": task.completed_at.isoformat(),
        "remaining": remaining,
    }


def get_task_details(db: Session, user_id: int, task_name: str) -> dict:
    employee = _get_employee(db, user_id)

    tasks = _all_tasks(db, employee.id)
    if not tasks:
        raise OnboardingServiceError(
            "No onboarding checklist has been created for this employee yet."
        )

    task = _resolve_one(tasks, "task_name", task_name, "onboarding task")

    due = _due_date(employee, task.due_day)
    return {
        "task_name": task.task_name,
        "category": task.category,
        "status": task.status,
        "due_date": due.isoformat() if due else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


# ---------------------------------------------------------------------------
# training
# ---------------------------------------------------------------------------
EXPIRY_WARNING_DAYS = 30


def _all_training(db: Session, employee_id: int) -> list[TrainingRecord]:
    return (
        db.query(TrainingRecord)
        .filter(TrainingRecord.employee_id == employee_id)
        .order_by(TrainingRecord.mandatory.desc(), TrainingRecord.course_name.asc())
        .all()
    )


def get_training_status(db: Session, user_id: int) -> dict:
    employee = _get_employee(db, user_id)

    records = _all_training(db, employee.id)
    if not records:
        raise OnboardingServiceError(
            "No training records have been created for this employee yet."
        )

    today = date.today()
    outstanding, completed, expiring = [], [], []

    for r in records:
        row = {
            "course_name": r.course_name,
            "mandatory": bool(r.mandatory),
            "status": r.status,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        }
        if r.status != "completed":
            outstanding.append(row)
            continue

        completed.append(row)
        # an expiry inside the warning window is the thing nobody tracks
        # themselves, so it is surfaced separately
        if r.expires_at:
            days = (r.expires_at - today).days
            if days <= EXPIRY_WARNING_DAYS:
                expiring.append({**row, "days_left": days, "expired": days < 0})

    return {
        "total": len(records),
        "outstanding": outstanding,
        "mandatory_outstanding": [r for r in outstanding if r["mandatory"]],
        "completed": completed,
        "expiring": expiring,
        "all_complete": not outstanding,
    }


def mark_training_complete(
    db: Session,
    user_id: int,
    course_name: str,
    expires_at: Optional[date] = None,
) -> dict:
    employee = _get_employee(db, user_id)

    records = _all_training(db, employee.id)
    if not records:
        raise OnboardingServiceError(
            "No training records have been created for this employee yet."
        )

    record = _resolve_one(records, "course_name", course_name, "training course")

    if record.status == "completed":
        raise OnboardingServiceError(
            f"'{record.course_name}' is already marked complete."
        )

    record.status = "completed"
    record.completed_at = date.today()
    if expires_at:
        record.expires_at = expires_at
    db.commit()
    db.refresh(record)

    return {
        "course_name": record.course_name,
        "completed_at": record.completed_at.isoformat(),
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
    }