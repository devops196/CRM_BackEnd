from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import LoginAttempt

class LoginAttemptService:
    def log_attempt(self, db: Session, **data):
        status_val = data.get("loginStatus")
        status_str = status_val.value if hasattr(status_val, "value") else str(status_val or "Allowed")
        item = LoginAttempt(
            loginstatus=status_str,
            name=data.get("name"),
            email=data.get("email") or "unknown@quickads.ai",
            profilepicture=data.get("profilePicture") or data.get("profilepicture"),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def get_attempts(self, db: Session, limit: int = 100):
        return db.scalars(
            select(LoginAttempt).order_by(LoginAttempt.timestamp.desc()).limit(limit)
        ).all()

login_attempt_service = LoginAttemptService()
