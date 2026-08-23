from datetime import datetime, timedelta, timezone
import random
import string

import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.config import settings
from app.models.user import User, Role, AccountStatus, LoginStatus
from app.services.login_attempt import login_attempt_service

def parse_expiry(value: str) -> timedelta:
    if value.endswith("d"):
        return timedelta(days=int(value[:-1]))
    if value.endswith("h"):
        return timedelta(hours=int(value[:-1]))
    if value.endswith("m"):
        return timedelta(minutes=int(value[:-1]))
    return timedelta(days=7)

class AuthService:
    def google_login(self, db: Session, id_token: str, ip_address=None, user_agent=None):
        try:
            payload = id_token_verify(id_token)
        except Exception:
            login_attempt_service.log_attempt(
                db, loginStatus=LoginStatus.REJECTED, reason="Invalid Google Token",
                ipAddress=ip_address, userAgent=user_agent
            )
            raise HTTPException(status_code=401, detail="Error - Use valid login credentials.")

        email = payload.get("email")
        name = payload.get("name")
        picture = payload.get("picture")
        domain = email.split("@", 1)[1] if email and "@" in email else None
        allowed = bool(email and email.endswith("@quickads.ai"))

        login_attempt_service.log_attempt(
            db, name=name, email=email, profilePicture=picture, domain=domain,
            loginStatus=LoginStatus.ALLOWED if allowed else LoginStatus.REJECTED,
            reason="Authenticated Successfully" if allowed else "Unauthorized email domain",
            ipAddress=ip_address, userAgent=user_agent
        )

        if not allowed:
            raise HTTPException(status_code=401, detail="Error - Use valid login credentials.")

        user = db.scalar(select(User).where(User.email == email))
        if user:
            if name:
                user.name = name
            if not user.picture and picture:
                user.picture = picture
        else:
            start = datetime.now(timezone.utc)
            end = start + timedelta(days=365)
            employee_id = "EMP-" + "".join(random.choices(string.digits, k=5))
            user = User(
                employeeId=employee_id, name=name or email.split("@")[0], email=email,
                picture=picture, role=Role.CUSTOMER, accountStatus=AccountStatus.ACTIVE,
                creditsAvailable=0, totalCredits=0,
                subscriptionStartDate=start, subscriptionEndDate=end
            )
            db.add(user)
        db.commit()
        db.refresh(user)

        jwt_payload = {
            "id": user.id, "employeeId": user.employeeId, "email": user.email,
            "role": user.role.value,
            "exp": datetime.now(timezone.utc) + parse_expiry(settings.JWT_EXPIRES_IN),
        }
        token = jwt.encode(jwt_payload, settings.JWT_SECRET, algorithm="HS256")
        return token, user

def id_token_verify(token: str):
    return id_token.verify_oauth2_token(
        token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
    )

auth_service = AuthService()
