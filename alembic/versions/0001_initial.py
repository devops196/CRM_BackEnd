"""Initial schema — User_details, login_attempt, UserTeamMember

Revision ID: 0001_initial
Revises: (none)

SAFE TO RUN ON EXISTING DATABASE:
This migration checks whether each table and ENUM type already exists
before trying to create them. If your database already has these tables
(e.g. created outside of Alembic), this migration will skip them safely.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def _enum_exists(conn, enum_name: str) -> bool:
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": enum_name},
    )
    return result.fetchone() is not None


def upgrade():
    conn = op.get_bind()

    # ── ENUM types (create only if they don't already exist) ──────────────
    if not _enum_exists(conn, "role"):
        PGEnum("ADMIN", "CUSTOMER", name="role").create(conn)

    if not _enum_exists(conn, "accountstatus"):
        PGEnum("ACTIVE", "INACTIVE", name="accountstatus").create(conn)

    if not _enum_exists(conn, "loginstatus"):
        PGEnum("ALLOWED", "REJECTED", name="loginstatus").create(conn)

    role = PGEnum("ADMIN", "CUSTOMER", name="role", create_type=False)
    account_status = PGEnum("ACTIVE", "INACTIVE", name="accountstatus", create_type=False)
    login_status = PGEnum("ALLOWED", "REJECTED", name="loginstatus", create_type=False)

    # ── User_details ───────────────────────────────────────────────────────
    if not _table_exists(conn, "User_details"):
        op.create_table(
            "User_details",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("employeeId", sa.String(), nullable=False, unique=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False, unique=True),
            sa.Column("role", role, nullable=False, server_default="CUSTOMER"),
            sa.Column("accountStatus", account_status, nullable=False, server_default="ACTIVE"),
            sa.Column("creditsAvailable", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("totalCredits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("subscriptionStartDate", sa.DateTime(timezone=True), nullable=False),
            sa.Column("subscriptionEndDate", sa.DateTime(timezone=True), nullable=False),
            sa.Column("picture", sa.String(), nullable=True),
            sa.Column("createdAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updatedAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    # ── login_attempt ──────────────────────────────────────────────────────
    # Note: the live DB uses the table name "LoginAttempt" (capital L/A).
    # We check both names to be safe.
    if not _table_exists(conn, "login_attempt") and not _table_exists(conn, "LoginAttempt"):
        op.create_table(
            "login_attempt",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("profilePicture", sa.String(), nullable=True),
            sa.Column("domain", sa.String(), nullable=True),
            sa.Column("loginStatus", login_status, nullable=False),
            sa.Column("reason", sa.String(), nullable=True),
            sa.Column("ipAddress", sa.String(), nullable=True),
            sa.Column("userAgent", sa.String(), nullable=True),
            sa.Column("attemptedAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    # ── UserTeamMember ─────────────────────────────────────────────────────
    if not _table_exists(conn, "UserTeamMember"):
        op.create_table(
            "UserTeamMember",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("ownerId", sa.String(), nullable=False),
            sa.Column("memberId", sa.String(), nullable=False),
            sa.Column("createdAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("ownerId", "memberId", name="uq_user_team_owner_member"),
        )


def downgrade():
    op.drop_table("UserTeamMember")
    op.drop_table("login_attempt")
    op.drop_table("User_details")
    op.execute("DROP TYPE IF EXISTS loginstatus")
    op.execute("DROP TYPE IF EXISTS accountstatus")
    op.execute("DROP TYPE IF EXISTS role")
