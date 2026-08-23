from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.services.users import user_service, team_service

router = APIRouter()

@router.get("/team")
def get_team(
    search: str | None = Query(None),
    role: str | None = Query(None),
    accountStatus: str | None = Query(None),
    creditRange: str | None = Query(None),
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

@router.get("/my-team")
def get_my_team(
    ownerEmail: str | None = Query(None),
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
    # DELETE supports JSON body here to preserve the original API.
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
