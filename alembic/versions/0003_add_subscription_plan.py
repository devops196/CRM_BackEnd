"""Add subscription_plan column to User_details

Revision ID: 0003_subscription_plan
Revises: 0002_credit_fields

SAFE TO RUN ON EXISTING DATABASE:
The column is only added if it does not already exist.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0003_subscription_plan"
down_revision = "0002_credit_fields"
branch_labels = None
depends_on = None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspect(conn).get_columns(table_name)}


def upgrade():
    conn = op.get_bind()
    if not _column_exists(conn, "User_details", "subscription_plan"):
        op.add_column(
            "User_details",
            sa.Column("subscription_plan", sa.String(100), nullable=True, server_default="discover"),
        )
        op.alter_column("User_details", "subscription_plan", server_default=None)


def downgrade():
    conn = op.get_bind()
    if _column_exists(conn, "User_details", "subscription_plan"):
        op.drop_column("User_details", "subscription_plan")
