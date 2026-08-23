from alembic import op
import sqlalchemy as sa

revision = '0002_credit_fields'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

columns = [
    ('generationcreditsused', sa.Integer(), 0), ('generationcreditstotal', sa.Integer(), 0),
    ('videocreditsused', sa.Integer(), 0), ('videocreditstotal', sa.Integer(), 0),
    ('voicecreditsused', sa.Integer(), 0), ('voiceclonecreditsused', sa.Integer(), 0),
    ('voicecreditstotal', sa.Integer(), 0), ('voiceclonecreditstotal', sa.Integer(), 0),
    ('analysiscreditsunlimited', sa.Boolean(), False),
    ('ugccreditsused', sa.Integer(), 0), ('ugccreditstotal', sa.Integer(), 0),
    ('imagecreditsused', sa.Integer(), 0), ('imagecreditstotal', sa.Integer(), 0),
    ('imagetovideocreditsused', sa.Integer(), 0), ('imagetovideocreditstotal', sa.Integer(), 0),
]

def upgrade():
    for name, typ, default in columns:
        op.add_column('User_details', sa.Column(name, typ, nullable=False, server_default=sa.text(str(default).lower() if isinstance(default, bool) else str(default))))
    for name, _, _ in columns:
        op.alter_column('User_details', name, server_default=None)

def downgrade():
    for name, _, _ in reversed(columns):
        op.drop_column('User_details', name)
