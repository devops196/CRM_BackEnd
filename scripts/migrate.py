"""
Smart migration runner for production deployments.

The problem this solves:
  The database already has tables with live data, but no 'alembic_version'
  table. When Alembic runs 'upgrade head' it tries to CREATE TABLE from
  scratch, which fails with DuplicateTable.

What this script does:
  1. Connects to the database.
  2. Checks if 'User_details' (our core table) exists.
  3. If it exists but 'alembic_version' does NOT exist, it stamps the DB
     to the current head revision so Alembic knows the schema is already
     up-to-date.
  4. Then runs 'alembic upgrade head' normally.
     - On a fresh database: runs all migrations.
     - On an already-stamped database: is a no-op (instant).
     - On a partially-migrated database: only runs the missing migrations.

Usage:
    python scripts/migrate.py
"""

import os
import subprocess
import sys


def get_engine():
    from sqlalchemy import create_engine
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # SSL required for Render external connections; not needed internally
    needs_ssl = "render.com" in url or "sslmode=require" in url
    connect_args = {"sslmode": "require"} if needs_ssl else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


def main() -> int:
    from sqlalchemy import inspect as sa_inspect

    print("==> Running smart migration check...")
    engine = get_engine()

    try:
        with engine.connect() as conn:
            inspector = sa_inspect(conn)
            has_alembic = inspector.has_table("alembic_version")
            has_users   = inspector.has_table("User_details")

        if has_users and not has_alembic:
            print(
                "==> Detected existing database with no Alembic version record.\n"
                "    Stamping database to head to avoid DuplicateTable errors..."
            )
            stamp = subprocess.run(
                [sys.executable, "-m", "alembic", "stamp", "head"],
                check=False,
            )
            if stamp.returncode != 0:
                # Fallback: try the alembic binary directly
                stamp = subprocess.run(["alembic", "stamp", "head"], check=True)
            print("==> Database stamped successfully.")
        elif has_alembic:
            print("==> alembic_version table found — normal upgrade path.")
        else:
            print("==> Fresh database — running full migration chain.")

    finally:
        engine.dispose()

    print("==> Running: alembic upgrade head")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        check=False,
    )

    if result.returncode != 0:
        # If upgrade still fails (very unlikely after stamp), try the Python module
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            check=False,
        )

    if result.returncode == 0:
        print("==> Migrations complete.")
    else:
        print("==> Migration failed — see errors above.", file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
