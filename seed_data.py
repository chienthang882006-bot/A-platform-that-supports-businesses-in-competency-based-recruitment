# FILE: seed_data.py
from datetime import datetime
from flask_bcrypt import Bcrypt

from database import db_session
from models import User, Student, StudentProfile, UserRole, Job, Company

bcrypt = Bcrypt()
db = db_session()

try:
    print("--- 🛠 ĐANG KHÔI PHỤC DỮ LIỆU ---")

    PASSWORD = "Th@nG1"

    # ======================================================
    # 1. STUDENT USER
    # ======================================================
    student_email = "baotv0798@ut.edu.vn"

    if not db.query(User).filter(User.email == student_email).first():
        student_user = User(
            email=student_email,
            password=bcrypt.generate_password_hash(PASSWORD).decode("utf-8"),
            role=UserRole.STUDENT,
            status="active"
        )
        db.add(student_user)
        db.commit()
        db.refresh(student_user)

        student = Student(
            userId=student_user.id,
            fullName="Bao Tran",
            dob=datetime(1998, 7, 9),
            major="Information Technology"
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        profile = StudentProfile(
            studentId=student.id,
            cvUrl="https://linkedin.com/in/baotv",
            about="Sinh viên test hệ thống LabOdc"
        )
        db.add(profile)
        db.commit()

        print("✅ STUDENT created:")
        print("   Email:", student_email)
        print("   Password:", PASSWORD)

    # ======================================================
    # 2. ADMIN USER
    # ======================================================
    admin_email = "admin@labodc.com"

    if not db.query(User).filter(User.email == admin_email).first():
        admin_user = User(
            email=admin_email,
            password=bcrypt.generate_password_hash(PASSWORD).decode("utf-8"),
            role=UserRole.ADMIN,
            status="active"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ ADMIN created:")
        print("   Email:", admin_email)
        print("   Password:", PASSWORD)

    # ======================================================
    # 3. COMPANY USER + COMPANY + JOBS
    # ======================================================
    company_email = "hr@labodc.com"

    if not db.query(User).filter(User.email == company_email).first():
        company_user = User(
            email=company_email,
            password=bcrypt.generate_password_hash(PASSWORD).decode("utf-8"),
            role=UserRole.COMPANY,
            status="active"
        )
        db.add(company_user)
        db.commit()
        db.refresh(company_user)

        company = Company(
            userId=company_user.id,
            companyName="LabOdc Tech"
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        jobs = [
            Job(
                companyId=company.id,
                title="Backend Developer (Python)",
                description="Phát triển hệ thống API với FastAPI.",
                location="HCM",
                status="open"
            ),
            Job(
                companyId=company.id,
                title="Frontend Developer",
                description="Xây dựng giao diện web.",
                location="Remote",
                status="open"
            )
        ]

        db.add_all(jobs)
        db.commit()

        print("✅ COMPANY created:")
        print("   Email:", company_email)
        print("   Password:", PASSWORD)
        print("   Jobs created")

except Exception as e:
    print("❌ ERROR:", e)
    db.rollback()

finally:
    db.close()
    print("--- ✅ HOÀN TẤT ---")
