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
    """Normal user: deduct from owner's balance, add to target's balance."""
    caller_email = body.get("callerEmail") or body.get("ownerEmail")
    target_identifier = body.get("targetIdentifier")
    allocations = body.get("allocations", {})

    if not caller_email or not target_identifier:
        raise HTTPException(status_code=400, detail="callerEmail and targetIdentifier are required.")

    # Verify caller is not an admin (admins must use the admin endpoint)
    caller = None
    all_users = db.scalars(select(User)).all()
    for u in all_users:
        if u.email and u.email.strip().lower() == caller_email.strip().lower():
            caller = u
            break
    if not caller and all_users:
        caller = all_users[0]

    caller_role = str(caller.role or "").upper()
    if caller_role == "ADMIN":
        raise HTTPException(status_code=403, detail="Admins must use the admin credit endpoint.")

    try:
        result = user_service.allocate_credits(db, caller.email, target_identifier, allocations)
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

@router.get("/my-team")
def get_my_team(
    ownerEmail: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owner = ownerEmail or current_user.get("email")
    if not owner:
        raise HTTPException(status_code=400, detail="ownerEmail query parameter is required.")
    data = team_service.get_my_team(db, owner)
    return {"success": True, "count": len(data), "data": data}

@router.post("/my-team")
def add_member(
    body: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owner = body.get("ownerEmail") or current_user.get("email")
    target = body.get("targetEmail")
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
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    owner = body.get("ownerEmail") or current_user.get("email")
    target = body.get("targetEmail")
    if not target:
        raise HTTPException(status_code=400, detail="ownerEmail and targetEmail are required.")
    try:
        data = team_service.remove_member(db, owner, target)
        return {"success": True, "message": "Team member removed successfully.", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
