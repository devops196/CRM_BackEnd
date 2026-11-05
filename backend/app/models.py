from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, ForeignKey, Integer, Text, Boolean, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False, default="Engineering", index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False, default="Employee")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active")
    app_role: Mapped[str] = mapped_column(String(30), nullable=False, default="Employee", index=True)
    joined_on: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(40), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="Pending", nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class CreditAllocation(Base):
    __tablename__ = "credit_allocations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    allocated_credits: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    used_credits: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Announcement(Base):
    __tablename__ = "announcements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
