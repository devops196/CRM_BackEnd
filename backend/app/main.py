import os
from datetime import date
from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import models, schemas
from .security import (
    create_access_token, verify_google_credential, get_current_employee, require_roles
)

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Internal CRM API",
    description="Internal CRM API: authentication, employee records, leave, credits, workflows, announcements and audit logs.",
    version="2.0.0",
)
origins = [os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

def log_action(db: Session, actor_id: int | None, action: str, entity_type: str, entity_id: int | None, details: dict | None = None):
    db.add(models.AuditLog(actor_employee_id=actor_id, action=action, entity_type=entity_type,
                           entity_id=entity_id, details=details or {}))

def ensure_employee(db: Session, employee_id: int):
    employee = db.get(models.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return employee

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "internal-crm-api"}

@app.post("/auth/google", tags=["Authentication"])
def google_login(payload: schemas.GoogleToken, db: Session = Depends(get_db)):
    info = verify_google_credential(payload.credential)
    email = info["email"].lower()
    employee = db.scalar(select(models.Employee).where(func.lower(models.Employee.email) == email))
    if not employee:
        # Safe default: only pre-provisioned employee records may sign in.
        raise HTTPException(status_code=403, detail="Your account is not provisioned. Contact HR or an administrator.")
    if employee.status not in ("Active", "On Leave"):
        raise HTTPException(status_code=403, detail="Your employee account is not active.")
    employee.google_sub = info.get("sub")
    db.commit()
    token = create_access_token(employee)
    return {"access_token": token, "token_type": "bearer", "user": {
        "id": employee.id, "full_name": employee.full_name, "email": employee.email,
        "app_role": employee.app_role, "department": employee.department
    }}

@app.get("/auth/me", tags=["Authentication"])
def auth_me(current: models.Employee = Depends(get_current_employee)):
    return {"id": current.id, "full_name": current.full_name, "email": current.email,
            "app_role": current.app_role, "department": current.department}

@app.get("/employees", response_model=list[schemas.EmployeeOut], tags=["Employees"])
def list_employees(search: str | None = Query(default=None, max_length=120), department: str | None = None,
                   db: Session = Depends(get_db), current: models.Employee = Depends(get_current_employee)):
    stmt = select(models.Employee).order_by(models.Employee.id.desc())
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(models.Employee.full_name.ilike(pattern) | models.Employee.email.ilike(pattern)
                          | models.Employee.role.ilike(pattern) | models.Employee.department.ilike(pattern))
    if department:
        stmt = stmt.where(models.Employee.department == department)
    return list(db.scalars(stmt).all())

@app.post("/employees", response_model=schemas.EmployeeOut, status_code=201, tags=["Employees"])
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db),
                    actor: models.Employee = Depends(require_roles("Admin", "HR"))):
    if payload.app_role not in ("Admin", "HR", "Employee"):
        raise HTTPException(status_code=422, detail="app_role must be Admin, HR, or Employee.")
    if actor.app_role != "Admin" and payload.app_role != "Employee":
        raise HTTPException(status_code=403, detail="Only an Admin can assign a privileged application role.")
    if actor.app_role != "Admin" and payload.status == "Inactive":
        raise HTTPException(status_code=403, detail="Only an Admin can create an inactive employee account.")
    employee = models.Employee(**payload.model_dump())
    db.add(employee)
    try:
        db.flush()
        log_action(db, actor.id, "employee.created", "employee", employee.id, {"email": employee.email})
        db.commit()
        db.refresh(employee)
        return employee
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An employee with this email already exists.")

@app.get("/employees/{employee_id}", response_model=schemas.EmployeeOut, tags=["Employees"])
def get_employee(employee_id: int, db: Session = Depends(get_db),
                 current: models.Employee = Depends(get_current_employee)):
    return ensure_employee(db, employee_id)

@app.patch("/employees/{employee_id}", response_model=schemas.EmployeeOut, tags=["Employees"])
def update_employee(employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db),
                    actor: models.Employee = Depends(require_roles("Admin", "HR"))):
    employee = ensure_employee(db, employee_id)
    changes = payload.model_dump(exclude_unset=True)
    if "app_role" in changes and changes["app_role"] not in ("Admin", "HR", "Employee"):
        raise HTTPException(status_code=422, detail="app_role must be Admin, HR, or Employee.")
    if "app_role" in changes and actor.app_role != "Admin":
        raise HTTPException(status_code=403, detail="Only an Admin can change application roles.")
    if changes.get("status") == "Inactive" and actor.app_role != "Admin":
        raise HTTPException(status_code=403, detail="Only an Admin can deactivate an employee account.")
    for key, value in changes.items():
        setattr(employee, key, value)
    log_action(db, actor.id, "employee.updated", "employee", employee.id, {"fields": list(changes.keys())})
    db.commit()
    db.refresh(employee)
    return employee

@app.delete("/employees/{employee_id}", status_code=204, tags=["Employees"])
def delete_employee(employee_id: int, db: Session = Depends(get_db),
                    actor: models.Employee = Depends(require_roles("Admin"))):
    employee = ensure_employee(db, employee_id)
    log_action(db, actor.id, "employee.deleted", "employee", employee.id, {"email": employee.email})
    employee.status = "Inactive"  # soft deactivate; preserve HR history
    db.commit()
    return Response(status_code=204)

@app.get("/dashboard", response_model=schemas.DashboardOut, tags=["Dashboard"])
def dashboard(db: Session = Depends(get_db), current: models.Employee = Depends(get_current_employee)):
    total = db.scalar(select(func.count()).select_from(models.Employee).where(models.Employee.status != "Inactive")) or 0
    active = db.scalar(select(func.count()).select_from(models.Employee).where(models.Employee.status == "Active")) or 0
    on_leave = db.scalar(select(func.count()).select_from(models.Employee).where(models.Employee.status == "On Leave")) or 0
    departments = db.scalar(select(func.count(func.distinct(models.Employee.department)).where(models.Employee.status != "Inactive"))) or 0
    return {"total_employees": total, "active_employees": active, "on_leave_today": on_leave, "departments": departments}

@app.get("/leaves", response_model=list[schemas.LeaveOut], tags=["Leave Management"])
def list_leaves(db: Session = Depends(get_db), current: models.Employee = Depends(get_current_employee)):
    stmt = select(models.LeaveRequest).order_by(models.LeaveRequest.created_at.desc())
    if current.app_role not in ("Admin", "HR"):
        stmt = stmt.where(models.LeaveRequest.employee_id == current.id)
    return list(db.scalars(stmt).all())

@app.post("/leaves", response_model=schemas.LeaveOut, status_code=201, tags=["Leave Management"])
def apply_leave(payload: schemas.LeaveCreate, db: Session = Depends(get_db),
                current: models.Employee = Depends(get_current_employee)):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="End date must be on or after start date.")
    item = models.LeaveRequest(employee_id=current.id, **payload.model_dump())
    db.add(item)
    db.flush()
    log_action(db, current.id, "leave.applied", "leave_request", item.id, {"leave_type": item.leave_type})
    db.commit()
    db.refresh(item)
    return item

@app.patch("/leaves/{leave_id}/review", response_model=schemas.LeaveOut, tags=["Leave Management"])
def review_leave(leave_id: int, payload: schemas.LeaveReview, db: Session = Depends(get_db),
                 actor: models.Employee = Depends(require_roles("Admin", "HR"))):
    if payload.status not in ("Approved", "Rejected"):
        raise HTTPException(status_code=422, detail="Status must be Approved or Rejected.")
    item = db.get(models.LeaveRequest, leave_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leave request not found.")
    if item.status != "Pending":
        raise HTTPException(status_code=409, detail="Only pending requests can be reviewed.")
    item.status, item.reviewed_by, item.review_note = payload.status, actor.id, payload.review_note
    log_action(db, actor.id, f"leave.{payload.status.lower()}", "leave_request", item.id)
    db.commit()
    db.refresh(item)
    return item

@app.get("/credits", response_model=list[schemas.CreditOut], tags=["Credits & Usage"])
def list_credits(db: Session = Depends(get_db), current: models.Employee = Depends(get_current_employee)):
    stmt = select(models.CreditAllocation).order_by(models.CreditAllocation.category)
    if current.app_role not in ("Admin", "HR"):
        stmt = stmt.where(models.CreditAllocation.employee_id == current.id)
    return list(db.scalars(stmt).all())

@app.post("/credits", response_model=schemas.CreditOut, status_code=201, tags=["Credits & Usage"])
def allocate_credits(payload: schemas.CreditCreate, db: Session = Depends(get_db),
                     actor: models.Employee = Depends(require_roles("Admin", "HR"))):
    ensure_employee(db, payload.employee_id)
    if payload.used_credits > payload.allocated_credits:
        raise HTTPException(status_code=422, detail="Used credits cannot exceed allocated credits.")
    item = models.CreditAllocation(**payload.model_dump())
    db.add(item)
    db.flush()
    log_action(db, actor.id, "credits.allocated", "credit_allocation", item.id,
               {"employee_id": item.employee_id, "category": item.category, "allocated": str(item.allocated_credits)})
    db.commit()
    db.refresh(item)
    return item

@app.patch("/credits/{credit_id}", response_model=schemas.CreditOut, tags=["Credits & Usage"])
def update_credits(credit_id: int, payload: schemas.CreditCreate, db: Session = Depends(get_db),
                   actor: models.Employee = Depends(require_roles("Admin", "HR"))):
    item = db.get(models.CreditAllocation, credit_id)
    if not item:
        raise HTTPException(status_code=404, detail="Credit allocation not found.")
    if payload.used_credits > payload.allocated_credits:
        raise HTTPException(status_code=422, detail="Used credits cannot exceed allocated credits.")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    log_action(db, actor.id, "credits.updated", "credit_allocation", item.id)
    db.commit()
    db.refresh(item)
    return item

@app.get("/announcements", response_model=list[schemas.AnnouncementOut], tags=["Announcements"])
def list_announcements(db: Session = Depends(get_db), current: models.Employee = Depends(get_current_employee)):
    return list(db.scalars(select(models.Announcement).where(models.Announcement.published.is_(True))
                           .order_by(models.Announcement.created_at.desc())).all())

@app.post("/announcements", response_model=schemas.AnnouncementOut, status_code=201, tags=["Announcements"])
def create_announcement(payload: schemas.AnnouncementCreate, db: Session = Depends(get_db),
                        actor: models.Employee = Depends(require_roles("Admin", "HR"))):
    item = models.Announcement(**payload.model_dump(), created_by=actor.id)
    db.add(item)
    db.flush()
    log_action(db, actor.id, "announcement.created", "announcement", item.id, {"title": item.title})
    db.commit()
    db.refresh(item)
    return item

@app.delete("/announcements/{announcement_id}", status_code=204, tags=["Announcements"])
def delete_announcement(announcement_id: int, db: Session = Depends(get_db),
                        actor: models.Employee = Depends(require_roles("Admin", "HR"))):
    item = db.get(models.Announcement, announcement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    log_action(db, actor.id, "announcement.deleted", "announcement", item.id)
    db.delete(item)
    db.commit()
    return Response(status_code=204)

@app.get("/workflows/{workflow_type}", response_model=list[schemas.TaskOut], tags=["Onboarding & Offboarding"])
def list_workflow_tasks(workflow_type: str, db: Session = Depends(get_db),
                        current: models.Employee = Depends(get_current_employee)):
    if workflow_type not in ("onboarding", "offboarding"):
        raise HTTPException(status_code=422, detail="workflow_type must be onboarding or offboarding.")
    stmt = select(models.WorkflowTask).where(models.WorkflowTask.workflow_type == workflow_type).order_by(models.WorkflowTask.created_at.desc())
    if current.app_role not in ("Admin", "HR"):
        stmt = stmt.where((models.WorkflowTask.employee_id == current.id) | (models.WorkflowTask.owner_id == current.id))
    return list(db.scalars(stmt).all())

@app.post("/workflows", response_model=schemas.TaskOut, status_code=201, tags=["Onboarding & Offboarding"])
def create_workflow_task(payload: schemas.TaskCreate, db: Session = Depends(get_db),
                         actor: models.Employee = Depends(require_roles("Admin", "HR"))):
    if payload.workflow_type not in ("onboarding", "offboarding"):
        raise HTTPException(status_code=422, detail="workflow_type must be onboarding or offboarding.")
    if payload.status not in ("Pending", "In Progress", "Completed", "Blocked"):
        raise HTTPException(status_code=422, detail="Invalid task status.")
    ensure_employee(db, payload.employee_id)
    if payload.owner_id is not None:
        ensure_employee(db, payload.owner_id)
    item = models.WorkflowTask(**payload.model_dump())
    db.add(item)
    db.flush()
    log_action(db, actor.id, f"{item.workflow_type}.task_created", "workflow_task", item.id)
    db.commit()
    db.refresh(item)
    return item

@app.patch("/workflows/tasks/{task_id}", response_model=schemas.TaskOut, tags=["Onboarding & Offboarding"])
def update_workflow_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db),
                         actor: models.Employee = Depends(get_current_employee)):
    item = db.get(models.WorkflowTask, task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Workflow task not found.")
    if actor.app_role not in ("Admin", "HR") and actor.id not in (item.employee_id, item.owner_id):
        raise HTTPException(status_code=403, detail="You cannot update this task.")
    changes = payload.model_dump(exclude_unset=True)
    if "status" in changes and changes["status"] not in ("Pending", "In Progress", "Completed", "Blocked"):
        raise HTTPException(status_code=422, detail="Invalid task status.")
    if actor.app_role not in ("Admin", "HR") and set(changes) - {"status"}:
        raise HTTPException(status_code=403, detail="Employees may update task status only. Contact HR to change task details.")
    if actor.app_role in ("Admin", "HR") and changes.get("owner_id") is not None:
        ensure_employee(db, changes["owner_id"])
    for key, value in changes.items():
        setattr(item, key, value)
    log_action(db, actor.id, f"{item.workflow_type}.task_updated", "workflow_task", item.id, {"fields": list(changes.keys())})
    db.commit()
    db.refresh(item)
    return item

@app.get("/audit-logs", tags=["Audit Logs"])
def list_audit_logs(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db),
                    actor: models.Employee = Depends(require_roles("Admin"))):
    rows = db.scalars(select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(limit)).all()
    return [{"id": x.id, "actor_employee_id": x.actor_employee_id, "action": x.action,
             "entity_type": x.entity_type, "entity_id": x.entity_id, "details": x.details,
             "created_at": x.created_at} for x in rows]
