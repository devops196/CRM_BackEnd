FROM python:3.12-slim

# Prevent .pyc files and enable unbuffered stdout/stderr for Render logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # PYTHONPATH ensures 'from app.xxx import ...' works from any working dir
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies first (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Start command:
#   1. scripts/migrate.py  — smart migration runner (handles existing tables safely)
#   2. uvicorn             — production ASGI server, binds to Render-injected $PORT
#
# NOTE: import_db.py is intentionally NOT run here.
#       It was a one-time data seeding script. Running it on every deploy
#       would overwrite live production data.
CMD ["sh", "-c", "python scripts/migrate.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
