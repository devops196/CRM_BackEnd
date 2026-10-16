import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CRM Backend API",
    version="1.0.0",
    # Disable interactive docs in production to avoid leaking API structure
    docs_url=None if settings.NODE_ENV == "production" else "/docs",
    redoc_url=None if settings.NODE_ENV == "production" else "/redoc",
)

# ---------------------------------------------------------------------------
# CORS — must allow the Vercel frontend domain plus localhost for development.
#
# IMPORTANT: When credentials (cookies) are involved you CANNOT use "*".
# Every origin must be listed explicitly.
# ---------------------------------------------------------------------------
_allowed_origins = list(
    dict.fromkeys(
        [
            settings.FRONTEND_URL,          # set to your Vercel URL in production
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,     # required for cookie-based auth
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],
)

app.include_router(router)


# ---------------------------------------------------------------------------
# Global exception handler — never leak stack traces in production
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error."},
    )


# ---------------------------------------------------------------------------
# Startup event — log useful info without exposing secrets
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info(
        "CRM API starting | env=%s | frontend=%s",
        settings.NODE_ENV,
        settings.FRONTEND_URL,
    )
