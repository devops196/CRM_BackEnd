from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

from app.config import settings
from app.db import Base
from app.models import user  # noqa: F401 — registers models with metadata

config = context.config

# Override alembic.ini sqlalchemy.url with the real DATABASE_URL from env.
# This means alembic.ini never needs real credentials hardcoded.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Render PostgreSQL requires SSL. Pass connect_args so migrations
# don't hang waiting for a non-SSL connection to be accepted.
_CONNECT_ARGS = {"sslmode": "require"} if "render.com" in settings.DATABASE_URL or "sslmode" in settings.DATABASE_URL else {}


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (outputs SQL only)."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the live database."""
    connectable = create_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
        connect_args=_CONNECT_ARGS,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
