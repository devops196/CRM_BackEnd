from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import LoginAttempt, LoginStatus

class LoginAttemptService:
    def log_attempt(self, db: Session, **data):
        item = LoginAttempt(
            loginStatus=data["loginStatus"],
            name=data.get("name"),
            email=data.get("email"),
            profilePicture=data.get("profilePicture"),
            domain=data.get("domain"),
            reason=data.get("reason"),
            ipAddress=data.get("ipAddress"),
            userAgent=data.get("userAgent"),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def get_attempts(self, db: Session, limit: int = 100):
        return db.scalars(
            select(LoginAttempt).order_by(LoginAttempt.attemptedAt.desc()).limit(limit)
        ).all()

login_attempt_service = LoginAttemptService()
