from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    role = sa.Enum("ADMIN", "CUSTOMER", name="role")
    account_status = sa.Enum("ACTIVE", "INACTIVE", name="accountstatus")
    login_status = sa.Enum("ALLOWED", "REJECTED", name="loginstatus")
    role.create(op.get_bind(), checkfirst=True)
    account_status.create(op.get_bind(), checkfirst=True)
    login_status.create(op.get_bind(), checkfirst=True)

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
