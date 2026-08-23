from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class GoogleLoginRequest(BaseModel):
    idToken: str = Field(min_length=1)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employeeId: str
    name: str
    email: str
    role: str
    accountStatus: str
    creditsAvailable: int
    totalCredits: int
    subscriptionStartDate: datetime
    subscriptionEndDate: datetime
    picture: str | None = None
    createdAt: datetime
    updatedAt: datetime

class TeamMemberResponse(UserResponse):
    usagePercentage: int
    remainingPercentage: int
    creditHealth: str

class LoginAttemptsResponse(BaseModel):
    success: bool
    count: int
    attempts: list[dict]
