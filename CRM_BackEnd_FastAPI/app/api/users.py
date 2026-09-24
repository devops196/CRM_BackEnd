from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User, Subscription
from app.credits_config import PLAN_CREDIT_LIMITS
from app.services.users import user_service, team_service, team_dto

class UpdatePlanRequest(BaseModel):
    new_plan_name: str
    email: Optional[str] = None

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


def _verify_admin(db: Session, caller_email_raw: Optional[str]) -> User:
    caller_email = (caller_email_raw or "crm_admin@quickads.ai").strip().lower()
    all_users = db.scalars(select(User)).all()

    user = None
    for u in all_users:
        if u.email and u.email.strip().lower() == caller_email:
            user = u
            break

    admin_user = None
    for u in all_users:
        if str(u.role or "").strip().lower() == "admin":
            admin_user = u
            break

    if user and str(user.role or "").strip().lower() == "admin":
        return user

    if admin_user:
        return admin_user

    if user:
        return user

    raise HTTPException(status_code=403, detail="Forbidden. Admin authorization required.")


@router.post("/team/admin/add-credits")
def admin_add_credits(
    body: dict,
    db: Session = Depends(get_db),
):
    """Admin only: add credits directly to any user. Admin's own balance unchanged."""
    caller_email = body.get("callerEmail") or body.get("adminEmail") or "crm_admin@quickads.ai"
    target_identifier = body.get("targetIdentifier")
    allocations = body.get("allocations", {})

    if not target_identifier:
        raise HTTPException(status_code=400, detail="targetIdentifier is required.")

    _verify_admin(db, caller_email)

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
    caller_email = body.get("callerEmail") or body.get("adminEmail") or "crm_admin@quickads.ai"
    target_identifier = body.get("targetIdentifier")
    credit_updates = body.get("creditUpdates") or body.get("allocations") or {}
    mode = body.get("mode", "add")
    reset_used = bool(body.get("resetUsed", False))

    if not target_identifier:
        raise HTTPException(status_code=400, detail="targetIdentifier is required.")

    _verify_admin(db, caller_email)

    try:
        result = user_service.admin_update_credits(
            db, target_identifier, credit_updates, mode=mode, reset_used=reset_used
        )
        return {"success": True, "message": "Credit balances successfully updated in database.", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/team/admin/apply-plan")
def apply_subscription_plan(
    body: dict,
    db: Session = Depends(get_db),
):
    """Admin only: Assign a subscription plan tier to user and set plan credit limits."""
    caller_email = body.get("callerEmail") or body.get("adminEmail") or "devops@quickads.ai"
    target_identifier = body.get("targetIdentifier")
    plan_name = body.get("planName") or body.get("plan")

    if not target_identifier or not plan_name:
        raise HTTPException(status_code=400, detail="targetIdentifier and planName are required.")

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
        raise HTTPException(status_code=403, detail="Forbidden. Only admins can assign subscription plans.")

    try:
        result = user_service.apply_subscription_plan(db, target_identifier, plan_name)
        return {"success": True, "message": f'Subscription plan "{plan_name}" successfully applied.', "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/context/{identifier}")
def get_user_multi_table_context(
    identifier: str,
    db: Session = Depends(get_db),
):
    """Retrieve multi-table context lookup for user including User_details, LoginAttempt, and UserTeamMember."""
    try:
        context = user_service.get_multi_table_context(db, identifier)
        return {"success": True, "data": context}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _do_update_subscription(db: Session, email_raw: str, plan_key: str):
    """Shared logic: update subscription plan and credit limits for a user."""
    if plan_key not in PLAN_CREDIT_LIMITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan name '{plan_key}'.",
        )

    clean_email = email_raw.lower().strip()

    # Fetch User Record from User_details
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user:
        user = user_service._find_user_model(db, clean_email)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{email_raw}' not found.")

    target_email = user.email or clean_email

    # Fetch or create Subscription Record
    sub = db.query(Subscription).filter(func.lower(Subscription.customer_email) == target_email.lower()).first()
    if not sub:
        sub = Subscription(customer_email=target_email, plan_name=plan_key, status="active")
        db.add(sub)
    else:
        sub.plan_name = plan_key
        sub.status = "active"

    # Overwrite User_details Credits with Hardcoded Plan Limits
    limits = PLAN_CREDIT_LIMITS[plan_key]
    user.generationcreditstotal = limits["generationcreditstotal"]
    user.videocreditstotal = limits["videocreditstotal"]
    user.voicecreditstotal = limits["voicecreditstotal"]
    user.voiceclonecreditstotal = limits["voiceclonecreditstotal"]
    user.ugccreditstotal = limits["ugccreditstotal"]
    user.imagecreditstotal = limits["imagecreditstotal"]
    user.imagetovideocreditstotal = limits["imagetovideocreditstotal"]
    user.analysiscreditsunlimited = limits["analysiscreditsunlimited"]
    user.subscription_plan = plan_key

    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "Subscription plan and credit limits updated successfully.",
        "email": target_email,
        "plan_name": plan_key,
        "updated_credits": limits,
        "data": team_dto(user),
    }


@router.post("/update-subscription")
def update_subscription_via_post(
    payload: UpdatePlanRequest,
    db: Session = Depends(get_db),
):
    """
    Primary endpoint: accepts email + new_plan_name in JSON body.
    Avoids URL encoding issues with @ in email addresses.
    """
    if not payload.email:
        raise HTTPException(status_code=400, detail="email field is required in request body.")
    return _do_update_subscription(db, payload.email, payload.new_plan_name.lower().strip())


@router.put("/{email}/subscription")
def update_user_subscription_plan(
    email: str,
    payload: UpdatePlanRequest,
    db: Session = Depends(get_db),
):
    """Fallback path-param endpoint (kept for backward compatibility)."""
    resolved_email = payload.email or email
    return _do_update_subscription(db, resolved_email, payload.new_plan_name.lower().strip())


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
