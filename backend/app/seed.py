import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func
from .database import SessionLocal, engine, Base
from . import models

def seed_database():
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Checking existing records...")
        existing_emails = {
            e.email.lower(): e for e in db.scalars(select(models.Employee)).all()
        }

        # 1. Employees to seed
        seed_employees_data = [
            {
                "full_name": "Devops Team",
                "email": "devops@quickads.ai",
                "department": "Operations",
                "role": "Administrator",
                "app_role": "Admin",
                "status": "Active",
                "phone": "+91 98765 00001",
                "joined_on": date(2024, 1, 15),
            },
            {
                "full_name": "Dhanush S",
                "email": "dhanush@quickads.ai",
                "department": "Engineering",
                "role": "Tech Intern",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00002",
                "joined_on": date(2026, 6, 1),
            },
            {
                "full_name": "Priya Sharma",
                "email": "priya.sharma@quickads.ai",
                "department": "HR",
                "role": "People Operations Lead",
                "app_role": "HR",
                "status": "Active",
                "phone": "+91 98765 00003",
                "joined_on": date(2024, 3, 10),
            },
            {
                "full_name": "Aarav Patel",
                "email": "aarav.patel@quickads.ai",
                "department": "Engineering",
                "role": "Senior Frontend Engineer",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00004",
                "joined_on": date(2024, 5, 20),
            },
            {
                "full_name": "Ananya Iyer",
                "email": "ananya.iyer@quickads.ai",
                "department": "Design",
                "role": "Lead Product Designer",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00005",
                "joined_on": date(2024, 8, 1),
            },
            {
                "full_name": "Rohan Mehta",
                "email": "rohan.mehta@quickads.ai",
                "department": "Product",
                "role": "Principal Product Manager",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00006",
                "joined_on": date(2024, 9, 15),
            },
            {
                "full_name": "Vikram Malhotra",
                "email": "vikram.malhotra@quickads.ai",
                "department": "Engineering",
                "role": "Backend Architect",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00007",
                "joined_on": date(2024, 11, 1),
            },
            {
                "full_name": "Neha Gupta",
                "email": "neha.gupta@quickads.ai",
                "department": "Marketing",
                "role": "Growth Marketing Specialist",
                "app_role": "Employee",
                "status": "On Leave",
                "phone": "+91 98765 00008",
                "joined_on": date(2025, 2, 10),
            },
            {
                "full_name": "Sneha Kulkarni",
                "email": "sneha.kulkarni@quickads.ai",
                "department": "HR",
                "role": "Talent Acquisition Specialist",
                "app_role": "HR",
                "status": "Active",
                "phone": "+91 98765 00009",
                "joined_on": date(2025, 4, 5),
            },
            {
                "full_name": "Siddharth Nair",
                "email": "siddharth.nair@quickads.ai",
                "department": "Sales",
                "role": "Enterprise Account Executive",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00010",
                "joined_on": date(2025, 6, 12),
            },
            {
                "full_name": "Tanvi Deshmukh",
                "email": "tanvi.deshmukh@quickads.ai",
                "department": "Finance",
                "role": "Senior Financial Analyst",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00011",
                "joined_on": date(2025, 8, 20),
            },
            {
                "full_name": "Karan Joshi",
                "email": "karan.joshi@quickads.ai",
                "department": "Operations",
                "role": "Site Reliability Engineer",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00012",
                "joined_on": date(2025, 10, 1),
            },
            {
                "full_name": "Pooja Reddy",
                "email": "pooja.reddy@quickads.ai",
                "department": "Customer Success",
                "role": "Customer Success Lead",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00013",
                "joined_on": date(2026, 1, 15),
            },
            {
                "full_name": "Arjun Kapoor",
                "email": "arjun.kapoor@quickads.ai",
                "department": "Engineering",
                "role": "Full Stack Developer",
                "app_role": "Employee",
                "status": "Active",
                "phone": "+91 98765 00014",
                "joined_on": date(2026, 3, 1),
            },
            {
                "full_name": "Meera Nambiar",
                "email": "meera.nambiar@quickads.ai",
                "department": "Product",
                "role": "Senior UX Researcher",
                "app_role": "Employee",
                "status": "Inactive",
                "phone": "+91 98765 00015",
                "joined_on": date(2023, 11, 1),
            },
        ]

        employee_map = {}
        for emp_data in seed_employees_data:
            email_lower = emp_data["email"].lower()
            if email_lower in existing_emails:
                emp = existing_emails[email_lower]
                # Update attributes if needed, preserving id
                for k, v in emp_data.items():
                    if k not in ("id", "email"):
                        setattr(emp, k, v)
                employee_map[email_lower] = emp
            else:
                emp = models.Employee(**emp_data)
                db.add(emp)
                db.flush()
                employee_map[email_lower] = emp

        db.commit()
        print(f"Total employees in database: {db.scalar(select(func.count(models.Employee.id)))}")

        # 2. Leave Requests
        existing_leaves_count = db.scalar(select(func.count(models.LeaveRequest.id)))
        if existing_leaves_count == 0:
            leaves_data = [
                {
                    "employee_id": employee_map["neha.gupta@quickads.ai"].id,
                    "leave_type": "Casual Leave",
                    "start_date": date.today(),
                    "end_date": date.today() + timedelta(days=2),
                    "reason": "Family function and travel back home.",
                    "status": "Approved",
                    "reviewed_by": employee_map["priya.sharma@quickads.ai"].id,
                    "review_note": "Approved. Have a safe journey!",
                },
                {
                    "employee_id": employee_map["aarav.patel@quickads.ai"].id,
                    "leave_type": "Sick Leave",
                    "start_date": date.today() + timedelta(days=5),
                    "end_date": date.today() + timedelta(days=6),
                    "reason": "Scheduled dental surgery and recovery.",
                    "status": "Pending",
                    "reviewed_by": None,
                    "review_note": None,
                },
                {
                    "employee_id": employee_map["dhanush@quickads.ai"].id,
                    "leave_type": "Work From Home",
                    "start_date": date.today() + timedelta(days=3),
                    "end_date": date.today() + timedelta(days=4),
                    "reason": "College semester exam presentations.",
                    "status": "Pending",
                    "reviewed_by": None,
                    "review_note": None,
                },
                {
                    "employee_id": employee_map["ananya.iyer@quickads.ai"].id,
                    "leave_type": "Earned Leave",
                    "start_date": date.today() - timedelta(days=14),
                    "end_date": date.today() - timedelta(days=10),
                    "reason": "Annual vacation.",
                    "status": "Approved",
                    "reviewed_by": employee_map["priya.sharma@quickads.ai"].id,
                    "review_note": "Approved.",
                },
            ]
            for l in leaves_data:
                db.add(models.LeaveRequest(**l))
            print(f"Added {len(leaves_data)} leave requests.")

        # 3. Credit Allocations
        existing_credits_count = db.scalar(select(func.count(models.CreditAllocation.id)))
        if existing_credits_count == 0:
            credits_data = [
                {"employee_id": employee_map["aarav.patel@quickads.ai"].id, "category": "Learning", "allocated_credits": Decimal("500.00"), "used_credits": Decimal("220.00")},
                {"employee_id": employee_map["dhanush@quickads.ai"].id, "category": "Learning", "allocated_credits": Decimal("300.00"), "used_credits": Decimal("50.00")},
                {"employee_id": employee_map["ananya.iyer@quickads.ai"].id, "category": "Wellness", "allocated_credits": Decimal("400.00"), "used_credits": Decimal("180.00")},
                {"employee_id": employee_map["vikram.malhotra@quickads.ai"].id, "category": "Home Office", "allocated_credits": Decimal("600.00"), "used_credits": Decimal("550.00")},
                {"employee_id": employee_map["priya.sharma@quickads.ai"].id, "category": "Recognition", "allocated_credits": Decimal("450.00"), "used_credits": Decimal("100.00")},
                {"employee_id": employee_map["devops@quickads.ai"].id, "category": "Learning", "allocated_credits": Decimal("1000.00"), "used_credits": Decimal("300.00")},
            ]
            for c in credits_data:
                db.add(models.CreditAllocation(**c))
            print(f"Added {len(credits_data)} credit allocations.")

        # 4. Announcements
        existing_announcements_count = db.scalar(select(func.count(models.Announcement.id)))
        if existing_announcements_count == 0:
            announcements_data = [
                {
                    "title": "Welcome to the New Quickads Internal CRM Platform!",
                    "body": "We are excited to roll out our centralized People Operations workspace. Track employee records, manage leave, monitor learning credits, and stay synchronized across teams.",
                    "created_by": employee_map["devops@quickads.ai"].id,
                    "published": True,
                },
                {
                    "title": "Annual Learning & Wellness Benefits Live",
                    "body": "Your annual benefit credits for this cycle have been allocated. You can use your allowance for courses, books, ergonomic equipment, and health memberships.",
                    "created_by": employee_map["priya.sharma@quickads.ai"].id,
                    "published": True,
                },
                {
                    "title": "All-Hands Meeting & Q4 Roadmap Review",
                    "body": "Join us this Friday at 4:00 PM IST for our company-wide town hall. We will celebrate team milestones, introduce joiners, and share our product roadmap.",
                    "created_by": employee_map["devops@quickads.ai"].id,
                    "published": True,
                },
            ]
            for a in announcements_data:
                db.add(models.Announcement(**a))
            print(f"Added {len(announcements_data)} announcements.")

        # 5. Workflow Tasks (Onboarding & Offboarding)
        existing_tasks_count = db.scalar(select(func.count(models.WorkflowTask.id)))
        if existing_tasks_count == 0:
            tasks_data = [
                {
                    "workflow_type": "onboarding",
                    "employee_id": employee_map["dhanush@quickads.ai"].id,
                    "title": "Setup developer workspace and cloud credentials",
                    "description": "Configure GitHub access, Render staging credentials, and dev environment.",
                    "owner_id": employee_map["devops@quickads.ai"].id,
                    "due_date": date.today() + timedelta(days=2),
                    "status": "In Progress",
                },
                {
                    "workflow_type": "onboarding",
                    "employee_id": employee_map["dhanush@quickads.ai"].id,
                    "title": "HR documentation and direct deposit setup",
                    "description": "Submit PAN/Aadhaar and bank account documentation on the portal.",
                    "owner_id": employee_map["priya.sharma@quickads.ai"].id,
                    "due_date": date.today() + timedelta(days=5),
                    "status": "Completed",
                },
                {
                    "workflow_type": "onboarding",
                    "employee_id": employee_map["arjun.kapoor@quickads.ai"].id,
                    "title": "Welcome coffee chat with Engineering lead",
                    "description": "Introduction to team ceremonies, sprint planning, and architecture standards.",
                    "owner_id": employee_map["vikram.malhotra@quickads.ai"].id,
                    "due_date": date.today() + timedelta(days=4),
                    "status": "Pending",
                },
                {
                    "workflow_type": "offboarding",
                    "employee_id": employee_map["meera.nambiar@quickads.ai"].id,
                    "title": "Knowledge transfer & Figma design system handover",
                    "description": "Handover all research repositories, Figma component libraries, and active design specs.",
                    "owner_id": employee_map["ananya.iyer@quickads.ai"].id,
                    "due_date": date.today() - timedelta(days=5),
                    "status": "Completed",
                },
                {
                    "workflow_type": "offboarding",
                    "employee_id": employee_map["meera.nambiar@quickads.ai"].id,
                    "title": "Revoke SSO and cloud account permissions",
                    "description": "Disable Google Workspace, Jira, AWS, and Render team access.",
                    "owner_id": employee_map["devops@quickads.ai"].id,
                    "due_date": date.today() - timedelta(days=3),
                    "status": "Completed",
                },
            ]
            for t in tasks_data:
                db.add(models.WorkflowTask(**t))
            print(f"Added {len(tasks_data)} workflow tasks.")

        # 6. Audit Logs
        existing_audit_count = db.scalar(select(func.count(models.AuditLog.id)))
        if existing_audit_count == 0:
            audit_data = [
                {
                    "actor_employee_id": employee_map["devops@quickads.ai"].id,
                    "action": "system.initialized",
                    "entity_type": "system",
                    "entity_id": 1,
                    "details": {"version": "2.0.0", "environment": "production"},
                },
                {
                    "actor_employee_id": employee_map["priya.sharma@quickads.ai"].id,
                    "action": "employee.created",
                    "entity_type": "employee",
                    "entity_id": employee_map["dhanush@quickads.ai"].id,
                    "details": {"role": "Tech Intern", "dept": "Engineering"},
                },
                {
                    "actor_employee_id": employee_map["devops@quickads.ai"].id,
                    "action": "announcement.published",
                    "entity_type": "announcement",
                    "entity_id": 1,
                    "details": {"title": "Welcome to the New Quickads Internal CRM Platform!"},
                },
            ]
            for a in audit_data:
                db.add(models.AuditLog(**a))
            print(f"Added {len(audit_data)} audit log records.")

        db.commit()
        print("Database seeded successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
