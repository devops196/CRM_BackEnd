from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserTeamMember


def team_dto(u: User) -> dict:
    total = u.generationcreditstotal or 0
    used = u.generationcreditsused or 0
    available = max(0, total - used)
    usage = min(100, round((used / total) * 100)) if total > 0 else 0
    remaining = min(100, round((available / total) * 100)) if total > 0 else 0
    health = "Critical" if remaining < 30 else "Warning" if remaining <= 70 else "Healthy"
    role_str = str(u.role or "user").upper()
    role_val = "ADMIN" if role_str == "ADMIN" else "CUSTOMER"

    return {
        "id": str(u.uuid),
        "employeeId": f"EMP-{str(u.uuid)[:8]}",
        "name": u.name or (u.email.split("@")[0] if u.email else "User"),
        "email": u.email or "",
        "role": role_val,
        "accountStatus": "ACTIVE",
        "creditsAvailable": available,
        "totalCredits": total,
        "picture": u.profilepicture,
        "subscriptionStartDate": "2026-01-01T00:00:00Z",
        "subscriptionEndDate": "2027-01-01T00:00:00Z",
        "generationcreditsused": u.generationcreditsused or 0,
        "generationcreditstotal": u.generationcreditstotal or 0,
        "videocreditsused": u.videocreditsused or 0,
        "videocreditstotal": u.videocreditstotal or 0,
        "voicecreditsused": u.voicecreditsused or 0,
        "voiceclonecreditsused": u.voiceclonecreditsused or 0,
        "voicecreditstotal": u.voicecreditstotal or 0,
        "voiceclonecreditstotal": u.voiceclonecreditstotal or 0,
        "analysiscreditsunlimited": bool(u.analysiscreditsunlimited),
        "ugccreditsused": u.ugccreditsused or 0,
        "ugccreditstotal": u.ugccreditstotal or 0,
        "imagecreditsused": u.imagecreditsused or 0,
        "imagecreditstotal": u.imagecreditstotal or 0,
        "imagetovideocreditsused": u.imagetovideocreditsused or 0,
        "imagetovideocreditstotal": u.imagetovideocreditstotal or 0,
        "usagePercentage": usage,
        "remainingPercentage": remaining,
        "creditHealth": health,
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
        q = str(user_id).strip().lower()
        for u in db.scalars(select(User)).all():
            if str(u.uuid).lower() == q or (u.email and u.email.lower() == q) or f"emp-{str(u.uuid)[:8]}".lower() == q:
                return team_dto(u)
        return None

    def _find_user_model(self, db: Session, identifier: str):
        """Internal helper: returns the SQLAlchemy User model instance."""
        q = str(identifier).strip().lower()
        for u in db.scalars(select(User)).all():
            uuid_str = str(u.uuid).lower()
            emp_id = f"emp-{uuid_str[:8]}"
            email_str = (u.email or "").lower()
            name_str = (u.name or "").lower()
            if (
                q == uuid_str
                or q == emp_id
                or q == email_str
                or q == name_str
                or (q.startswith("emp-") and uuid_str.startswith(q[4:]))
                or (len(q) >= 4 and uuid_str.startswith(q))
            ):
                return u
        return None

    def get_user_by_identifier(self, db: Session, identifier: str):
        u = self._find_user_model(db, identifier)
        return team_dto(u) if u else None

    def allocate_credits(self, db: Session, owner_email: str, target_identifier: str, allocations: dict):
        """Normal user: deducts from owner, adds to target."""
        owner = None
        for u in db.scalars(select(User)).all():
            if u.email and u.email.strip().lower() == owner_email.strip().lower():
                owner = u
                break
        if not owner:
            raise ValueError(f'Owner user "{owner_email}" was not found.')

        target = self._find_user_model(db, target_identifier)
        if not target:
            raise ValueError(f'Target user "{target_identifier}" was not found.')
        if str(owner.uuid) == str(target.uuid):
            raise ValueError("You cannot allocate credits to yourself.")

        # (used_field, total_field) — we deduct from owner's *total*, add to target's *total*
        field_map = {
            "generationCredits": ("generationcreditsused", "generationcreditstotal"),
            "videoCredits": ("videocreditsused", "videocreditstotal"),
            "voiceCredits": ("voicecreditsused", "voicecreditstotal"),
            "voiceCloneCredits": ("voiceclonecreditsused", "voiceclonecreditstotal"),
            "ugcCredits": ("ugccreditsused", "ugccreditstotal"),
            "imageCredits": ("imagecreditsused", "imagecreditstotal"),
            "imageToVideoCredits": ("imagetovideocreditsused", "imagetovideocreditstotal"),
        }

        for key, val in allocations.items():
            count = int(val or 0)
            if count <= 0 or key not in field_map:
                continue
            used_field, total_field = field_map[key]
            owner_total = getattr(owner, total_field) or 0
            owner_used = getattr(owner, used_field) or 0
            owner_avail = max(0, owner_total - owner_used)
            if count > owner_avail:
                raise ValueError(f'Insufficient credits for {key}. Available: {owner_avail}, Requested: {count}')
            # Deduct from owner by increasing their used count
            setattr(owner, used_field, owner_used + count)
            # Give to target by increasing their total
            target_total = getattr(target, total_field) or 0
            setattr(target, total_field, target_total + count)

        db.commit()
        db.refresh(owner)
        db.refresh(target)
        return team_dto(target)

    def admin_add_credits(self, db: Session, target_identifier: str, allocations: dict):
        """Admin: adds credits directly to target. Admin's own credits unchanged."""
        target = self._find_user_model(db, target_identifier)
        if not target:
            raise ValueError(f'Target user "{target_identifier}" was not found.')

        field_map = {
            "generationCredits": "generationcreditstotal",
            "videoCredits": "videocreditstotal",
            "voiceCredits": "voicecreditstotal",
            "voiceCloneCredits": "voiceclonecreditstotal",
            "ugcCredits": "ugccreditstotal",
            "imageCredits": "imagecreditstotal",
            "imageToVideoCredits": "imagetovideocreditstotal",
        }

        for key, val in allocations.items():
            count = int(val or 0)
            if count <= 0 or key not in field_map:
                continue
            total_field = field_map[key]
            current_total = getattr(target, total_field) or 0
            setattr(target, total_field, current_total + count)

        db.commit()
        db.refresh(target)
        return team_dto(target)


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
