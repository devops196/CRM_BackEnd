from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(users_router, prefix="/users", tags=["Users"])

@router.get("/health/", tags=["Health"])
def health():
    return {"success": True, "message": "API is running"}
