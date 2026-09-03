from datetime import datetime
from enum import Enum
from typing import Optional
import uuid
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text, UniqueConstraint, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

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

    uuid: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True, unique=True)
    profilepicture: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)

    generationcreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generationcreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    videocreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    videocreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voicecreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voiceclonecreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voicecreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voiceclonecreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    analysiscreditsunlimited: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ugccreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ugccreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagecreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagecreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagetovideocreditsused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imagetovideocreditstotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscription_plan: Mapped[Optional[str]] = mapped_column(String(100), default="discover", nullable=True)

    @property
    def id(self) -> str:
        return str(self.uuid)

    @property
    def employeeId(self) -> str:
        return f"EMP-{str(self.uuid)[:8]}"

    @property
    def picture(self) -> Optional[str]:
        return self.profilepicture

    @property
    def creditsAvailable(self) -> int:
        return max(0, (self.generationcreditstotal or 0) - (self.generationcreditsused or 0))

    @property
    def totalCredits(self) -> int:
        return self.generationcreditstotal or 0

    @property
    def subscriptionStartDate(self) -> str:
        return "2026-01-01T00:00:00Z"

    @property
    def subscriptionEndDate(self) -> str:
        return "2027-01-01T00:00:00Z"

    @property
    def accountStatus(self) -> str:
        return "ACTIVE"


class LoginAttempt(Base):
    __tablename__ = "LoginAttempt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    profilepicture: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    loginstatus: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    @property
    def profilePicture(self) -> Optional[str]:
        return self.profilepicture

    @property
    def loginStatus(self) -> str:
        return (self.loginstatus or "ALLOWED").upper()

    @property
    def domain(self) -> Optional[str]:
        return self.email.split("@", 1)[1] if self.email and "@" in self.email else None

    @property
    def reason(self) -> str:
        return "Authenticated Successfully" if (self.loginstatus or "").lower() == "allowed" else "Unauthorized"

    @property
    def ipAddress(self) -> str:
        return "127.0.0.1"

    @property
    def userAgent(self) -> Optional[str]:
        return None

    @property
    def attemptedAt(self) -> Optional[datetime]:
        return self.timestamp


class UserTeamMember(Base):
    __tablename__ = "UserTeamMember"
    __table_args__ = (UniqueConstraint("ownerId", "memberId", name="uq_user_team_owner_member"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    ownerId: Mapped[str] = mapped_column(String, nullable=False)
    memberId: Mapped[str] = mapped_column(String, nullable=False)
    createdAt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    customer_email = Column(String(255), ForeignKey("User_details.email", ondelete="CASCADE"), nullable=False)
    plan_name = Column(String(100), nullable=False)
    status = Column(String(50), default="active")
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserDomainAssociation(Base):
    __tablename__ = "user_domain_association"

    association_id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(PG_UUID(as_uuid=False), ForeignKey("User_details.uuid", ondelete="CASCADE"), nullable=False)
    domain_name = Column(String(255))
    role = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
