from datetime import datetime, timezone
from sqlalchemy import select

from app.db import SessionLocal
from app.models.user import User, Role, AccountStatus

seed_users = [
    ("EMP-1001", "Devops Team", "devops@quickads.ai", Role.CUSTOMER, AccountStatus.ACTIVE, 1200, 1500, "2026-01-01", "2027-12-31"),
    ("EMP-1002", "CRM Tester", "crmtester@quickads.ai", Role.CUSTOMER, AccountStatus.ACTIVE, 500, 600, "2026-02-01", "2027-02-01"),
    ("EMP-1003", "Rajesh Kesevan", "rajesh@quickads.ai", Role.ADMIN, AccountStatus.ACTIVE, 1880, 5000, "2026-01-15", "2027-01-15"),
    ("EMP-1004", "Alex Turner", "alex@quickads.ai", Role.CUSTOMER, AccountStatus.ACTIVE, 2550, 3000, "2026-03-20", "2027-03-20"),
    ("EMP-1005", "Sarah Mitchell", "sarah@quickads.ai", Role.CUSTOMER, AccountStatus.INACTIVE, 250, 2000, "2025-06-10", "2026-06-10"),
]

db = SessionLocal()
try:
    for emp, name, email, role, status, available, total, start, end in seed_users:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.name, user.role, user.accountStatus = name, role, status
        else:
            user = User(
                employeeId=emp, name=name, email=email, role=role, accountStatus=status,
                creditsAvailable=available, totalCredits=total,
                subscriptionStartDate=datetime.fromisoformat(start).replace(tzinfo=timezone.utc),
                subscriptionEndDate=datetime.fromisoformat(end).replace(tzinfo=timezone.utc),
                picture=None,
            )
            db.add(user)
    db.commit()
    print("Database seeded successfully.")
finally:
    db.close()
