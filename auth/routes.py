from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from db.database import get_db
from db.models import User, Employee, LeaveBalance, OnboardingTask, TrainingRecord
from auth.security import hash_password, verify_password, create_access_token
from auth.dependencies import validate_password_strength

router = APIRouter()

DEFAULT_LEAVE_BALANCES = {"sick": 12, "casual": 12, "earned": 18}


DEFAULT_ONBOARDING = [
    ("Submit PAN card", "documents", 3),
    ("Submit bank details", "documents", 3),
    ("Submit address proof", "documents", 5),
    ("Complete IT setup", "it", 1),
    ("Sign code of conduct", "compliance", 7),
]
DEFAULT_TRAINING = [
    ("Data Protection", True),
    ("Workplace Safety", True),
    ("Anti-Harassment", True),
]


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    validate_password_strength(request.password)

    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=request.username, hashed_password=hash_password(request.password)
    )

    db.add(user)
    db.flush()

    employee = Employee(user_id=user.id)
    db.add(employee)
    db.flush()

    for leave_type, total_days in DEFAULT_LEAVE_BALANCES.items():
        db.add(
            LeaveBalance(
                employee_id=employee.id,
                leave_type=leave_type,
                total_days=total_days,
                used_days=0,
            )
        )

    for name, cat, day in DEFAULT_ONBOARDING:
        db.add(
            OnboardingTask(
                employee_id=employee.id, task_name=name, category=cat, due_day=day
            )
        )
    for name, mand in DEFAULT_TRAINING:
        db.add(
            TrainingRecord(employee_id=employee.id, course_name=name, mandatory=mand)
        )

    db.commit()
    return {"status": "registered", "username": user.username}


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or passowrd.")

    access_token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=access_token)
