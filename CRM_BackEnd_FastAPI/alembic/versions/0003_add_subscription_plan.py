"""Add subscription_plan column to User_details table

Revision ID: 0003_subscription_plan
Revises: 0002_credit_fields
"""

from alembic import op
import sqlalchemy as sa

revision = '0003_subscription_plan'
down_revision = '0002_credit_fields'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('User_details', sa.Column('subscription_plan', sa.String(100), nullable=True, server_default='discover'))
    op.alter_column('User_details', 'subscription_plan', server_default=None)

def downgrade():
    op.drop_column('User_details', 'subscription_plan')
