"""Add per-credit-type columns to User_details

Revision ID: 0002_credit_fields
Revises: 0001_initial

SAFE TO RUN ON EXISTING DATABASE:
Each column is only added if it does not already exist.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_credit_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

# (column_name, type, server_default)
COLUMNS = [
    ("generationcreditsused",       sa.Integer(), "0"),
    ("generationcreditstotal",      sa.Integer(), "0"),
    ("videocreditsused",            sa.Integer(), "0"),
    ("videocreditstotal",           sa.Integer(), "0"),
    ("voicecreditsused",            sa.Integer(), "0"),
    ("voiceclonecreditsused",       sa.Integer(), "0"),
    ("voicecreditstotal",           sa.Integer(), "0"),
    ("voiceclonecreditstotal",      sa.Integer(), "0"),
    ("analysiscreditsunlimited",    sa.Boolean(), "false"),
    ("ugccreditsused",              sa.Integer(), "0"),
    ("ugccreditstotal",             sa.Integer(), "0"),
    ("imagecreditsused",            sa.Integer(), "0"),
    ("imagecreditstotal",           sa.Integer(), "0"),
    ("imagetovideocreditsused",     sa.Integer(), "0"),
    ("imagetovideocreditstotal",    sa.Integer(), "0"),
]


def _existing_columns(conn, table_name: str) -> set:
    return {col["name"] for col in inspect(conn).get_columns(table_name)}


def upgrade():
    conn = op.get_bind()
    existing = _existing_columns(conn, "User_details")

    for name, typ, default in COLUMNS:
        if name not in existing:
            op.add_column(
                "User_details",
                sa.Column(name, typ, nullable=False, server_default=sa.text(default)),
            )
            # Remove server_default after adding so column becomes plain nullable-free
            op.alter_column("User_details", name, server_default=None)


def downgrade():
    conn = op.get_bind()
    existing = _existing_columns(conn, "User_details")
    for name, _, _ in reversed(COLUMNS):
        if name in existing:
            op.drop_column("User_details", name)
