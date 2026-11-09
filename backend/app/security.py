import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from google.oauth2 import id_token
from google.auth.transport import requests

from sqlalchemy.orm import Session

from .database import get_db
from . import models
import logging

logger = logging.getLogger(__name__)

# Load backend/.env explicitly
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=True)


# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

bearer = HTTPBearer(auto_error=False)


def create_access_token(employee: models.Employee) -> str:
    secret = os.getenv("JWT_SECRET", JWT_SECRET)
    if not secret or len(secret) < 32:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET must be set to a random secret of at least 32 characters in Render Environment settings."
        )

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(employee.id),
        "email": employee.email,
        "role": employee.app_role,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }

    return jwt.encode(
        payload,
        secret,
        algorithm=JWT_ALGORITHM
    )


def verify_google_credential(credential: str) -> dict:
    raw_client_ids = os.getenv("GOOGLE_CLIENT_ID", GOOGLE_CLIENT_ID)
    if not raw_client_ids:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID is missing in Render Environment settings."
        )

    client_ids = [c.strip() for c in raw_client_ids.split(",") if c.strip()]
    audience = client_ids[0] if len(client_ids) == 1 else client_ids

    try:
        info = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            audience
        )

        print("Google token audience:", info.get("aud"))
        print("Expected audience:", GOOGLE_CLIENT_ID)
        print("Google token issuer:", info.get("iss"))

    except Exception as e:
        print("GOOGLE VERIFICATION ERROR:", repr(e))

        raise HTTPException(
            status_code=401,
            detail=f"Google verification failed: {type(e).__name__}: {str(e)}"
        )

    if not info.get("email") or not info.get("email_verified"):
        raise HTTPException(
            status_code=401,
            detail="Verified Google email is required."
        )

    return info

def get_current_employee(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.Employee:

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    secret = os.getenv("JWT_SECRET", JWT_SECRET)
    if not secret or len(secret) < 32:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET is not configured."
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=[JWT_ALGORITHM]
        )

        employee_id = int(payload["sub"])

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token."
        )

    employee = db.get(models.Employee, employee_id)

    if not employee or employee.status == "Inactive":
        raise HTTPException(
            status_code=401,
            detail="User account is not active."
        )

    return employee


def require_roles(*roles: str):

    def role_dependency(
        employee: models.Employee = Depends(get_current_employee)
    ):

        if employee.app_role not in roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action."
            )

        return employee

    return role_dependency