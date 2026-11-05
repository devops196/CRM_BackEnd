# Internal CRM Pro Backend

FastAPI + SQLAlchemy + Pydantic + PostgreSQL API. See the project root `README.md` for full setup, OAuth configuration, roles, and production hardening notes.

Quick start (Windows PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env, then:
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for Swagger UI. Do not use real employee data until your team has completed security and privacy review.
