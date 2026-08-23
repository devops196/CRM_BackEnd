from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.api.auth import router as auth_router
from app.api.users import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(users_router, prefix="/users", tags=["Users"])

@router.get("/health/", tags=["Health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"success": True, "message": "API is running", "database": "connected"}
    except Exception as e:
        return {"success": False, "message": f"Database error: {str(e)}", "database": "disconnected"}
