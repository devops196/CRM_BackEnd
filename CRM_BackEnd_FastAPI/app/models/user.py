from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

class Role(str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"

class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class LoginStatus(str, Enum):
    ALLOWED = "ALLOWED"
    REJECTED = "REJECTED"

class User(Base):
    __tablename__ = "User_details"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    employeeId: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    role: Mapped[Role] = mapped_column(SAEnum(Role, name="role"), default=Role.CUSTOMER, nullable=False)
    accountStatus: Mapped[AccountStatus] = mapped_column(SAEnum(AccountStatus, name="accountstatus"), default=AccountStatus.ACTIVE, nullable=False)
    creditsAvailable: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    totalCredits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscriptionStartDate: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    subscriptionEndDate: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    picture: Mapped[str | None] = mapped_column(String, nullable=True)
    generationcreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generationcreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    videocreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    videocreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voicecreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voiceclonecreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voicecreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voiceclonecreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    analysiscreditsunlimited: Mapped[bool] = mapped_column(nullable=False, default=False)
    ugccreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ugccreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagecreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagecreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagetovideocreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagetovideocreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class LoginAttempt(Base):
    __tablename__ = "login_attempt"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    profilePicture: Mapped[str | None] = mapped_column(String, nullable=True)
    domain: Mapped[str | None] = mapped_column(String, nullable=True)
    loginStatus: Mapped[LoginStatus] = mapped_column(SAEnum(LoginStatus, name="loginstatus"), nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    ipAddress: Mapped[str | None] = mapped_column(String, nullable=True)
    userAgent: Mapped[str | None] = mapped_column(String, nullable=True)
    attemptedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class UserTeamMember(Base):
    __tablename__ = "UserTeamMember"
    __table_args__ = (UniqueConstraint("ownerId", "memberId", name="uq_user_team_owner_member"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    ownerId: Mapped[str] = mapped_column(String, nullable=False)
    memberId: Mapped[str] = mapped_column(String, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
