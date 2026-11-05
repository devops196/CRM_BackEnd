from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    department: str = Field(min_length=2, max_length=100)
    role: str = Field(min_length=2, max_length=100)
    status: str = "Active"
    app_role: str = "Employee"
    joined_on: date = Field(default_factory=date.today)
    phone: str | None = None

class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    department: str | None = None
    role: str | None = None
    status: str | None = None
    app_role: str | None = None
    phone: str | None = None

class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    department: str
    role: str
    status: str
    app_role: str
    joined_on: date
    phone: str | None = None
    created_at: datetime

class GoogleToken(BaseModel):
    credential: str

class LeaveCreate(BaseModel):
    leave_type: str = Field(min_length=2, max_length=40)
    start_date: date
    end_date: date
    reason: str | None = None

class LeaveReview(BaseModel):
    status: str
    review_note: str | None = None

class LeaveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None
    status: str
    reviewed_by: int | None
    review_note: str | None
    created_at: datetime

class CreditCreate(BaseModel):
    category: str = Field(min_length=2, max_length=100)
    employee_id: int
    allocated_credits: Decimal = Field(ge=0)
    used_credits: Decimal = Field(default=Decimal("0"), ge=0)

class CreditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: str
    employee_id: int
    allocated_credits: Decimal
    used_credits: Decimal
    updated_at: datetime

class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    body: str = Field(min_length=2)
    published: bool = True

class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    body: str
    created_by: int | None
    published: bool
    created_at: datetime

class TaskCreate(BaseModel):
    workflow_type: str
    employee_id: int
    title: str = Field(min_length=2, max_length=180)
    description: str | None = None
    owner_id: int | None = None
    due_date: date | None = None
    status: str = "Pending"

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    owner_id: int | None = None
    due_date: date | None = None
    status: str | None = None

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workflow_type: str
    employee_id: int
    title: str
    description: str | None
    owner_id: int | None
    due_date: date | None
    status: str
    created_at: datetime

class DashboardOut(BaseModel):
    total_employees: int
    active_employees: int
    on_leave_today: int
    departments: int
