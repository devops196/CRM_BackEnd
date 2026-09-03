from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.user import User, UserTeamMember, LoginAttempt, Subscription, UserDomainAssociation
from app.credits_config import get_plan_credit_limits


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
        "subscriptionPlan": getattr(u, "subscription_plan", None) or "discover",
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
    def ensure_plan_credits(self, db: Session, user: User) -> User:
        """
        Auto-sync helper — two separate concerns:
        1. ALWAYS: sync user.subscription_plan from the subscriptions table.
           If no subscriptions record exists, create one using user.subscription_plan or 'discover'.
        2. ONLY WHEN ALL credits are zero (brand new user):
           Initialize credit totals from PLAN_CREDIT_LIMITS for the active plan.
           This preserves any manually added credits — it never overwrites non-zero values.
        """
        if not user or not user.email:
            return user

        email_clean = user.email.strip().lower()
        sub = db.scalar(select(Subscription).where(func.lower(Subscription.customer_email) == email_clean))

        if sub and sub.plan_name:
            active_plan = sub.plan_name.strip().lower()
        else:
            active_plan = (getattr(user, "subscription_plan", None) or "discover").strip().lower()
            sub = Subscription(customer_email=user.email, plan_name=active_plan, status="active")
            db.add(sub)

        changed = False

        # Always sync the subscription_plan field on User_details
        if getattr(user, "subscription_plan", None) != active_plan:
            user.subscription_plan = active_plan
            changed = True

        # Only initialize credits if this is a brand new user (ALL totals are zero)
        all_zero = (
            (user.generationcreditstotal or 0) == 0
            and (user.videocreditstotal or 0) == 0
            and (user.voicecreditstotal or 0) == 0
            and (user.ugccreditstotal or 0) == 0
        )
        if all_zero:
            limits = get_plan_credit_limits(active_plan)
            user.generationcreditstotal = limits["generationcreditstotal"]
            user.videocreditstotal = limits["videocreditstotal"]
            user.voicecreditstotal = limits["voicecreditstotal"]
            user.voiceclonecreditstotal = limits["voiceclonecreditstotal"]
            user.ugccreditstotal = limits["ugccreditstotal"]
            user.imagecreditstotal = limits["imagecreditstotal"]
            user.imagetovideocreditstotal = limits["imagetovideocreditstotal"]
            user.analysiscreditsunlimited = limits["analysiscreditsunlimited"]
            changed = True

        if changed:
            try:
                db.commit()
                db.refresh(user)
            except Exception:
                db.rollback()

        return user

    def get_team_members(self, db: Session, search=None, role=None, accountStatus=None, creditRange=None):
        users = db.scalars(select(User).order_by(User.name.asc())).all()
        for u in users:
            self.ensure_plan_credits(db, u)
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
                if (u.generationcreditstotal or 0) == 0:
                    self.ensure_plan_credits(db, u)
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
        if u and (u.generationcreditstotal or 0) == 0:
            self.ensure_plan_credits(db, u)
        return team_dto(u) if u else None

    def allocate_credits(self, db: Session, owner_email: str, target_identifier: str, allocations: dict):
        """Allocate credits from owner's balance to target member in database."""
        q_owner = (owner_email or "").strip().lower()
        owner = None
        for u in db.scalars(select(User)).all():
            if u.email and u.email.strip().lower() == q_owner:
                owner = u
                break
        if not owner:
            for u in db.scalars(select(User)).all():
                if str(u.role or "").upper() == "ADMIN":
                    owner = u
                    break
        if not owner:
            owner = User(
                email=owner_email,
                name=owner_email.split("@")[0].capitalize(),
                role="ADMIN",
                generationcreditstotal=200,
                generationcreditsused=0
            )
            db.add(owner)
            db.commit()
            db.refresh(owner)

        target = self._find_user_model(db, target_identifier)
        if not target:
            raise ValueError(f'Target user "{target_identifier}" was not found.')
        if str(owner.uuid) == str(target.uuid):
            raise ValueError("You cannot allocate credits to yourself.")

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

            # Deduct from owner by increasing their used count or total
            setattr(owner, used_field, owner_used + count)
            # Give to target by increasing target total
            target_total = getattr(target, total_field) or 0
            setattr(target, total_field, target_total + count)

        db.commit()
        db.refresh(owner)
        db.refresh(target)
        return team_dto(target)

    def admin_add_credits(self, db: Session, target_identifier: str, allocations: dict):
        """Admin: adds credits directly to target. Admin's own credits unchanged."""
        return self.admin_update_credits(db, target_identifier, allocations, mode="add")

    def admin_update_credits(self, db: Session, target_identifier: str, credit_updates: dict, mode: str = "add", reset_used: bool = False):
        """Admin: update or set credit totals for target user in the database."""
        target = self._find_user_model(db, target_identifier)
        if not target:
            raise ValueError(f'Target user "{target_identifier}" was not found.')

        total_field_map = {
            "generationCredits": "generationcreditstotal",
            "videoCredits": "videocreditstotal",
            "voiceCredits": "voicecreditstotal",
            "voiceCloneCredits": "voiceclonecreditstotal",
            "ugcCredits": "ugccreditstotal",
            "imageCredits": "imagecreditstotal",
            "imageToVideoCredits": "imagetovideocreditstotal",
        }

        used_field_map = {
            "generationCredits": "generationcreditsused",
            "videoCredits": "videocreditsused",
            "voiceCredits": "voicecreditsused",
            "voiceCloneCredits": "voiceclonecreditsused",
            "ugcCredits": "ugccreditsused",
            "imageCredits": "imagecreditsused",
            "imageToVideoCredits": "imagetovideocreditstotal",
        }

        for key, val in credit_updates.items():
            if key not in total_field_map:
                continue
            count = int(val or 0)
            total_field = total_field_map[key]
            current_total = getattr(target, total_field) or 0

            if mode == "set":
                setattr(target, total_field, max(0, count))
            else:
                if count > 0:
                    setattr(target, total_field, current_total + count)

            if reset_used:
                used_field = used_field_map[key]
                setattr(target, used_field, 0)

        db.commit()
        db.refresh(target)
        return team_dto(target)

    def apply_subscription_plan(self, db: Session, target_identifier: str, plan_name: str):
        """
        Assign a subscription plan tier to target user and update all credit limits accordingly.
        """
        target = self._find_user_model(db, target_identifier)
        if not target:
            raise ValueError(f'Target user "{target_identifier}" was not found.')

        limits = get_plan_credit_limits(plan_name)
        target.generationcreditstotal = limits["generationcreditstotal"]
        target.videocreditstotal = limits["videocreditstotal"]
        target.voicecreditstotal = limits["voicecreditstotal"]
        target.voiceclonecreditstotal = limits["voiceclonecreditstotal"]
        target.ugccreditstotal = limits["ugccreditstotal"]
        target.imagecreditstotal = limits["imagecreditstotal"]
        target.imagetovideocreditstotal = limits["imagetovideocreditstotal"]
        target.analysiscreditsunlimited = limits["analysiscreditsunlimited"]
        target.subscription_plan = plan_name.strip().lower()

        db.commit()
        db.refresh(target)
        return team_dto(target)

    def get_multi_table_context(self, db: Session, identifier: str) -> dict:
        """
        Perform a multi-table lookup aggregating User_details, subscriptions, user_domain_association, LoginAttempt, and UserTeamMember records.
        """
        target = self._find_user_model(db, identifier)
        if not target:
            raise ValueError(f'User with identifier "{identifier}" was not found.')

        user_email = (target.email or "").strip().lower()

        # 1. Query subscriptions table
        sub_record = None
        if user_email:
            sub = db.scalar(
                select(Subscription).where(func.lower(Subscription.customer_email) == user_email)
            )
            if sub:
                sub_record = {
                    "id": str(sub.id),
                    "customer_email": sub.customer_email,
                    "plan_name": sub.plan_name,
                    "status": sub.status,
                    "start_date": sub.start_date.isoformat() if sub.start_date else None,
                    "end_date": sub.end_date.isoformat() if sub.end_date else None,
                    "created_at": sub.created_at.isoformat() if sub.created_at else None,
                    "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
                }

        # 2. Query user_domain_association table
        domain_associations = []
        if target.uuid:
            target_uuid = str(target.uuid)
            associations = db.scalars(
                select(UserDomainAssociation).where(UserDomainAssociation.user_id == target_uuid)
            ).all()
            for da in associations:
                domain_associations.append({
                    "association_id": str(da.association_id),
                    "user_id": str(da.user_id),
                    "domain_name": da.domain_name,
                    "role": da.role,
                    "created_at": da.created_at.isoformat() if da.created_at else None,
                })

        # 3. Query login attempts for user email
        login_attempts = []
        if user_email:
            attempts = db.scalars(
                select(LoginAttempt)
                .where(func.lower(LoginAttempt.email) == user_email)
                .order_by(LoginAttempt.timestamp.desc())
            ).all()
            for la in attempts:
                login_attempts.append({
                    "id": la.id,
                    "name": la.name,
                    "email": la.email,
                    "loginStatus": la.loginStatus,
                    "timestamp": la.timestamp.isoformat() if la.timestamp else None,
                    "reason": la.reason,
                    "domain": la.domain,
                    "ipAddress": la.ipAddress,
                })

        # 4. Query team memberships where user is owner or member
        team_memberships = []
        if user_email:
            memberships = db.scalars(
                select(UserTeamMember).where(
                    (func.lower(UserTeamMember.ownerId) == user_email) |
                    (func.lower(UserTeamMember.memberId) == user_email)
                )
            ).all()
            for tm in memberships:
                team_memberships.append({
                    "id": tm.id,
                    "ownerId": tm.ownerId,
                    "memberId": tm.memberId,
                    "createdAt": tm.createdAt.isoformat() if tm.createdAt else None,
                })

        return {
            "user": team_dto(target),
            "subscription": sub_record,
            "domainAssociations": domain_associations,
            "loginAttempts": login_attempts,
            "teamMemberships": team_memberships,
            "summary": {
                "totalLoginAttempts": len(login_attempts),
                "successfulLogins": sum(1 for la in login_attempts if la["loginStatus"] == "ALLOWED"),
                "rejectedLogins": sum(1 for la in login_attempts if la["loginStatus"] != "ALLOWED"),
                "teamMembershipsCount": len(team_memberships),
                "domainAssociationsCount": len(domain_associations),
                "activePlan": sub_record["plan_name"] if sub_record else (target.subscription_plan or "discover"),
            },
        }


user_service = UserService()


class TeamManagementService:
    def get_my_team(self, db: Session, owner_email: str):
        owner = (owner_email or "").strip().lower()
        if not owner:
            return []
        links = db.scalars(select(UserTeamMember).where(func.lower(UserTeamMember.ownerId) == owner)).all()
        if not links:
            return []
        member_emails = [x.memberId.strip().lower() for x in links if x.memberId]
        if not member_emails:
            return []
        users = db.scalars(select(User).where(func.lower(User.email).in_(member_emails)).order_by(User.name.asc())).all()
        return [team_dto(u) for u in users]

    def add_member(self, db: Session, owner_email: str, target_email: str):
        owner = (owner_email or "").strip().lower()
        target = (target_email or "").strip().lower()
        if not owner or not target:
            raise ValueError("ownerEmail and targetEmail are required.")
        if owner == target:
            raise ValueError("You cannot add yourself to your team.")
        
        user = db.scalar(select(User).where(func.lower(User.email) == target))
        if not user:
            for u in db.scalars(select(User)).all():
                if u.email and u.email.strip().lower() == target:
                    user = u
                    break
        if not user:
            raise ValueError(f'User with email "{target_email}" was not found in database.')

        target_actual_email = user.email.strip().lower()

        existing = db.scalar(select(UserTeamMember).where(
            func.lower(UserTeamMember.ownerId) == owner,
            func.lower(UserTeamMember.memberId) == target_actual_email
        ))
        if not existing:
            db.add(UserTeamMember(ownerId=owner, memberId=target_actual_email))
            db.commit()
        return self.get_my_team(db, owner)

    def remove_member(self, db: Session, owner_email: str, target_email: str):
        owner = (owner_email or "").strip().lower()
        target = (target_email or "").strip().lower()
        if not owner or not target:
            raise ValueError("ownerEmail and targetEmail are required.")

        links = db.scalars(select(UserTeamMember).where(
            func.lower(UserTeamMember.ownerId) == owner,
            func.lower(UserTeamMember.memberId) == target
        )).all()
        for link in links:
            db.delete(link)
        db.commit()
        return self.get_my_team(db, owner)


team_service = TeamManagementService()
()
