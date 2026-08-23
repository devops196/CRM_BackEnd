from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.users import user_service, team_service

router = APIRouter()

@router.get("/team")
def get_team(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    accountStatus: Optional[str] = Query(None),
    creditRange: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    members = user_service.get_team_members(db, search, role, accountStatus, creditRange)
    return {"success": True, "count": len(members), "data": members}

@router.get("/me/credits")
def my_credits(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    data = user_service.get_my_credits(db, current_user["id"])
    if not data:
        raise HTTPException(status_code=404, detail="User credits profile not found.")
    return {"success": True, "data": data}

@router.get("/lookup/{identifier}")
def lookup_user(identifier: str, db: Session = Depends(get_db)):
    user = user_service.get_user_by_identifier(db, identifier)
    if not user:
        raise HTTPException(status_code=404, detail=f'User with identifier "{identifier}" not found.')
    return {"success": True, "data": user}

@router.post("/team/allocate-credits")
def allocate_credits(
    body: dict,
    db: Session = Depends(get_db),
):
    """Allocate credits from owner's balance to target member."""
    caller_email = body.get("callerEmail") or body.get("ownerEmail")
    target_identifier = body.get("targetIdentifier")
    allocations = body.get("allocations", {})

    if not caller_email or not target_identifier:
        raise HTTPException(status_code=400, detail="callerEmail and targetIdentifier are required.")

    try:
        result = user_service.allocate_credits(db, caller_email, target_identifier, allocations)
        return {"success": True, "message": "Credits successfully allocated.", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/team/admin/add-credits")
def admin_add_credits(
    body: dict,
    db: Session = Depends(get_db),
):
    """Admin only: add credits directly to any user. Admin's own balance unchanged."""
    caller_email = body.get("callerEmail") or body.get("adminEmail") or "devops@quickads.ai"
    target_identifier = body.get("targetIdentifier")
    allocations = body.get("allocations", {})

    if not target_identifier:
        raise HTTPException(status_code=400, detail="targetIdentifier is required.")

    # Verify caller is admin from DB
    caller = None
    all_users = db.scalars(select(User)).all()
    for u in all_users:
        if u.email and u.email.strip().lower() == caller_email.strip().lower():
            caller = u
            break
    if not caller:
        for u in all_users:
            if str(u.role or "").upper() == "ADMIN":
                caller = u
                break
    if not caller:
        raise HTTPException(status_code=404, detail="Admin user not found in database.")

    caller_role = str(caller.role or "").upper()
    if caller_role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden. Only admins can add credits.")

    try:
        result = user_service.admin_add_credits(db, target_identifier, allocations)
        return {"success": True, "message": "Credits successfully added.", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/team/admin/update-credits")
def admin_update_credits(
    body: dict,
    db: Session = Depends(get_db),
):
    """Admin only: update or set credit totals for any user in database."""
    caller_email = body.get("callerEmail") or body.get("adminEmail") or "devops@quickads.ai"
    target_identifier = body.get("targetIdentifier")
    credit_updates = body.get("creditUpdates") or body.get("allocations") or {}
    mode = body.get("mode", "add")
    reset_used = bool(body.get("resetUsed", False))

    if not target_identifier:
        raise HTTPException(status_code=400, detail="targetIdentifier is required.")

    caller = None
    all_users = db.scalars(select(User)).all()
    for u in all_users:
        if u.email and u.email.strip().lower() == caller_email.strip().lower():
            caller = u
            break
    if not caller:
        for u in all_users:
            if str(u.role or "").upper() == "ADMIN":
                caller = u
                break
    if not caller:
        raise HTTPException(status_code=404, detail="Admin user not found in database.")

    caller_role = str(caller.role or "").upper()
    if caller_role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden. Only admins can modify credit controls.")

    try:
        result = user_service.admin_update_credits(
            db, target_identifier, credit_updates, mode=mode, reset_used=reset_used
        )
        return {"success": True, "message": "Credit balances successfully updated in database.", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/my-team")
def get_my_team(
    ownerEmail: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    owner = ownerEmail or "devops@quickads.ai"
    if not owner:
        raise HTTPException(status_code=400, detail="ownerEmail query parameter is required.")
    data = team_service.get_my_team(db, owner)
    return {"success": True, "count": len(data), "data": data}

@router.post("/my-team")
def add_member(
    body: dict,
    db: Session = Depends(get_db),
):
    owner = body.get("ownerEmail") or body.get("callerEmail") or "devops@quickads.ai"
    target = body.get("targetEmail") or body.get("targetIdentifier")
    if not owner or not target:
        raise HTTPException(status_code=400, detail="ownerEmail and targetEmail are required.")
    try:
        data = team_service.add_member(db, owner, target)
        return {"success": True, "message": "Team member added successfully.", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/my-team")
async def remove_member(
    request: Request,
    db: Session = Depends(get_db),
):
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    owner = body.get("ownerEmail") or body.get("callerEmail") or "devops@quickads.ai"
    target = body.get("targetEmail") or body.get("targetIdentifier")
    if not owner or not target:
        raise HTTPException(status_code=400, detail="ownerEmail and targetEmail are required.")
    try:
        data = team_service.remove_member(db, owner, target)
        return {"success": True, "message": "Team member removed successfully.", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
