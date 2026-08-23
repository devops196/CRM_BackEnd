from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserTeamMember

def team_dto(u: User) -> dict:
    total = u.totalCredits or 0
    available = u.creditsAvailable or 0
    used = max(0, total - available)
    usage = min(100, round((used / total) * 100)) if total > 0 else 0
    remaining = min(100, round((available / total) * 100)) if total > 0 else 0
    health = "Critical" if remaining < 30 else "Warning" if remaining <= 70 else "Healthy"
    return {
        "id": u.id, "employeeId": u.employeeId, "name": u.name, "email": u.email,
        "role": u.role.value, "accountStatus": u.accountStatus.value,
        "creditsAvailable": u.creditsAvailable, "totalCredits": u.totalCredits,
        "picture": u.picture, "subscriptionStartDate": u.subscriptionStartDate,
        "subscriptionEndDate": u.subscriptionEndDate,
        "generationcreditsused": u.generationcreditsused, "generationcreditstotal": u.generationcreditstotal,
        "videocreditsused": u.videocreditsused, "videocreditstotal": u.videocreditstotal,
        "voicecreditsused": u.voicecreditsused, "voiceclonecreditsused": u.voiceclonecreditsused,
        "voicecreditstotal": u.voicecreditstotal, "voiceclonecreditstotal": u.voiceclonecreditstotal,
        "analysiscreditsunlimited": u.analysiscreditsunlimited,
        "ugccreditsused": u.ugccreditsused, "ugccreditstotal": u.ugccreditstotal,
        "imagecreditsused": u.imagecreditsused, "imagecreditstotal": u.imagecreditstotal,
        "imagetovideocreditsused": u.imagetovideocreditsused,
        "imagetovideocreditstotal": u.imagetovideocreditstotal,
        "usagePercentage": usage,
        "remainingPercentage": remaining, "creditHealth": health,
    }

class UserService:
    def get_team_members(self, db: Session, search=None, role=None, accountStatus=None, creditRange=None):
        users = db.scalars(select(User).order_by(User.name.asc())).all()
        result = [team_dto(u) for u in users]
        if search and search.strip():
            q = search.strip().lower()
            result = [m for m in result if q in m["name"].lower() or q in m["email"].lower() or q in m["employeeId"].lower()]
        if role and role.lower() != "all":
            result = [m for m in result if m["role"].upper() == role.upper()]
        if accountStatus and accountStatus.lower() != "all":
            result = [m for m in result if m["accountStatus"].upper() == accountStatus.upper()]
        if creditRange and creditRange.lower() != "all":
            result = [m for m in result if m["creditHealth"].lower() == creditRange.lower()]
        return result

    def get_my_credits(self, db: Session, user_id: str):
        user = db.scalar(select(User).where(User.id == user_id))
        return team_dto(user) if user else None

user_service = UserService()

class TeamManagementService:
    def get_my_team(self, db: Session, owner_email: str):
        owner = owner_email.strip().lower()
        links = db.scalars(select(UserTeamMember).where(UserTeamMember.ownerId == owner)).all()
        if not links:
            return []
        emails = [x.memberId for x in links]
        users = db.scalars(select(User).where(User.email.in_(emails)).order_by(User.name.asc())).all()
        return [team_dto(u) for u in users]

    def add_member(self, db: Session, owner_email: str, target_email: str):
        owner, target = owner_email.strip().lower(), target_email.strip().lower()
        if owner == target:
            raise ValueError("You cannot add yourself to your team.")
        user = db.scalar(select(User).where(User.email == target))
        if not user:
            raise ValueError(f'User with email "{target_email}" was not found in database.')
        existing = db.scalar(select(UserTeamMember).where(
            UserTeamMember.ownerId == owner, UserTeamMember.memberId == target
        ))
        if not existing:
            db.add(UserTeamMember(ownerId=owner, memberId=target))
            db.commit()
        return self.get_my_team(db, owner)

    def remove_member(self, db: Session, owner_email: str, target_email: str):
        owner, target = owner_email.strip().lower(), target_email.strip().lower()
        links = db.scalars(select(UserTeamMember).where(
            UserTeamMember.ownerId == owner, UserTeamMember.memberId == target
        )).all()
        for link in links:
            db.delete(link)
        db.commit()
        return self.get_my_team(db, owner)

team_service = TeamManagementService()
