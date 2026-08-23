from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import router

app = FastAPI(title="CRM Backend API", version="1.0.0")

allowed_origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"success": False, "message": "Internal server error."})
