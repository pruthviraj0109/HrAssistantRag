from sqlalchemy import (
    Column,
    INTEGER,
    String,
    DateTime,
    Date,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(INTEGER, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="user", uselist=False)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(INTEGER, primary_key=True, index=True)
    user_id = Column(INTEGER, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    role = Column(String, nullable=True)
    joining_date = Column(Date, nullable=True)  # <-- new
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="employee")
    leave_balances = relationship("LeaveBalance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    onboarding_tasks = relationship("OnboardingTask", back_populates="employee")
    training_records = relationship("TrainingRecord", back_populates="employee")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(INTEGER, primary_key=True, index=True)
    employee_id = Column(INTEGER, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String, nullable=False)  # e.g. "sick", "casual", "earned"
    total_days = Column(INTEGER, nullable=False)
    used_days = Column(INTEGER, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    employee = relationship("Employee", back_populates="leave_balances")

    @property
    def remaining_days(self) -> int:
        return self.total_days - self.used_days


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(INTEGER, primary_key=True, index=True)
    employee_id = Column(INTEGER, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(
        String, nullable=False, default="pending"
    )  
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="leave_requests")


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id = Column(INTEGER, primary_key=True, index=True)
    employee_id = Column(INTEGER, ForeignKey("employees.id"), nullable=False)
    task_name = Column(String, nullable=False)
    category = Column(String, nullable=True)  # documents / it / hr / compliance
    due_day = Column(INTEGER, nullable=True)  # days from joining
    status = Column(String, nullable=False, default="pending")  # pending | done
    completed_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="onboarding_tasks")


class TrainingRecord(Base):
    __tablename__ = "training_records"

    id = Column(INTEGER, primary_key=True, index=True)
    employee_id = Column(INTEGER, ForeignKey("employees.id"), nullable=False)
    course_name = Column(String, nullable=False)
    mandatory = Column(Boolean, nullable=False, default=False)
    status = Column(String, nullable=False, default="pending")  # pending | completed
    completed_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="training_records")
