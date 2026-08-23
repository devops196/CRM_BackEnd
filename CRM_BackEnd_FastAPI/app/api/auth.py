from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import GoogleLoginRequest, UserResponse
from app.services.auth import auth_service
from app.services.login_attempt import login_attempt_service

router = APIRouter()

@router.post("/google")
def google_login(data: GoogleLoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else None)
    ua = request.headers.get("user-agent")
    token, user = auth_service.google_login(db, data.idToken, ip, ua)
    response.set_cookie(
        key=settings.COOKIE_NAME, value=token, httponly=True,
        secure=settings.NODE_ENV == "production", samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    return {"success": True, "message": "Login successful.", "user": UserResponse.model_validate(user).model_dump(mode="json")}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.COOKIE_NAME)
    return {"success": True, "message": "Logged out successfully."}

@router.get("/me")
def me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"success": True, "user": UserResponse.model_validate(user).model_dump(mode="json")}

@router.get("/login-attempts")
def login_attempts(db: Session = Depends(get_db)):
    attempts = login_attempt_service.get_attempts(db)
    data = []
    for x in attempts:
        data.append({
            "id": x.id, "name": x.name, "email": x.email, "profilePicture": x.profilePicture,
            "domain": x.domain, "loginStatus": x.loginStatus.value, "reason": x.reason,
            "ipAddress": x.ipAddress, "userAgent": x.userAgent,
            "attemptedAt": x.attemptedAt.isoformat() if x.attemptedAt else None,
        })
    return {"success": True, "count": len(data), "attempts": data}
