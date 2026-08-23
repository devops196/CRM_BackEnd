import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import select

from app.db import SessionLocal
from app.models.user import User, LoginAttempt, Role, AccountStatus, LoginStatus

ROOT = Path(__file__).resolve().parents[1]


def as_int(v):
    return int(v or 0)


def import_users(db):
    path = ROOT / 'data_User_details.csv'
    with path.open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            email = row['email'].strip().lower()
            user = db.scalar(select(User).where(User.email == email))
            role = Role.ADMIN if email.startswith('crm_admin@') or row['name'].strip().lower() == 'admin' else Role.CUSTOMER
            now = datetime.now(timezone.utc)
            values = dict(
                id=str(row['id']), employeeId=f"EMP-{row['id']}", name=row['name'], email=email,
                role=role, accountStatus=AccountStatus.ACTIVE,
                creditsAvailable=max(0, as_int(row['generationcreditstotal']) - as_int(row['generationcreditsused'])),
                totalCredits=as_int(row['generationcreditstotal']),
                subscriptionStartDate=now, subscriptionEndDate=now + timedelta(days=365),
                picture=row.get('profilepicture') or None,
                generationcreditsused=as_int(row['generationcreditsused']),
                generationcreditstotal=as_int(row['generationcreditstotal']),
                videocreditsused=as_int(row['videocreditsused']),
                videocreditstotal=as_int(row['videocreditstotal']),
                voicecreditsused=as_int(row['voicecreditsused']),
                voiceclonecreditsused=as_int(row['voiceclonecreditsused']),
                voicecreditstotal=as_int(row['voicecreditstotal']),
                voiceclonecreditstotal=as_int(row['voiceclonecreditstotal']),
                analysiscreditsunlimited=str(row['analysiscreditsunlimited']).lower() == 'true',
                ugccreditsused=as_int(row['ugccreditsused']), ugccreditstotal=as_int(row['ugccreditstotal']),
                imagecreditsused=as_int(row['imagecreditsused']), imagecreditstotal=as_int(row['imagecreditstotal']),
                imagetovideocreditsused=as_int(row['imagetovideocreditsused']),
                imagetovideocreditstotal=as_int(row['imagetovideocreditstotal']),
            )
            if user:
                for k, v in values.items():
                    if k != 'id': setattr(user, k, v)
            else:
                db.add(User(**values))


def import_login_attempts(db):
    path = ROOT / 'data_LoginAttempt.csv'
    with path.open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            existing = db.get(LoginAttempt, str(row['id']))
            status = LoginStatus.ALLOWED if row['loginstatus'].strip().lower() == 'allowed' else LoginStatus.REJECTED
            timestamp = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            values = dict(id=str(row['id']), name=row.get('name') or None, email=row.get('email') or None,
                          profilePicture=row.get('profilepicture') or None, loginStatus=status,
                          reason='Imported from existing database', attemptedAt=timestamp)
            if existing:
                for k, v in values.items(): setattr(existing, k, v)
            else:
                db.add(LoginAttempt(**values))


def main():
    db = SessionLocal()
    try:
        import_users(db)
        import_login_attempts(db)
        db.commit()
        print('CRM database imported successfully.')
    finally:
        db.close()

if __name__ == '__main__':
    main()
