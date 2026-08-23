# CRM Backend — Python FastAPI

Node.js + Express + Prisma backend converted to:

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2
- Alembic
- PostgreSQL
- PyJWT
- Google OAuth verification

## Run

```powershell
cd CRM_BackEnd_FastAPI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Update `.env` with your PostgreSQL and Google credentials.

Create/update database schema:

```powershell
alembic upgrade head
```

Start API:

```powershell
uvicorn app.main:app --reload --port 8000
```

Swagger:
`http://localhost:8000/docs`

## API compatibility

The original `/api/v1` routes are preserved:

- `GET /api/v1/health/`
- `POST /api/v1/auth/google`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/login-attempts`
- `GET /api/v1/users/team`
- `GET /api/v1/users/me/credits`
- `GET /api/v1/users/my-team`
- `POST /api/v1/users/my-team`
- `DELETE /api/v1/users/my-team`

Authentication still uses an HTTP-only cookie, so the existing frontend can continue using cookie-based auth.

## Imported Database

The project now includes the supplied database exports:

- `data_User_details.csv` — 3 users
- `data_LoginAttempt.csv` — 1 login attempt

After `alembic upgrade head`, run:

```powershell
python scripts/import_db.py
```

The Docker startup command runs the migration and import automatically.

The imported credit fields are preserved for generation, video, voice, voice clone, UGC, image, image-to-video, and unlimited analysis credits.
