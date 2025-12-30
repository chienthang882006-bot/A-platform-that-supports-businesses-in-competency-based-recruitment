# FILE: seed_data.py
from database import SessionLocal
from models import User, Student, StudentProfile, UserRole, Job, Company
from datetime import datetime

# 1. Khởi tạo session
db = SessionLocal()

try:
    print("--- 🛠 ĐANG KHÔI PHỤC DỮ LIỆU ---")

    # ==========================================
    # 1. TẠO TÀI KHOẢN CỦA BẠN (baotv0798)
    # ==========================================
    my_email = "baotv0798@ut.edu.vn"
    
    # Kiểm tra xem đã có chưa (để tránh lỗi chạy 2 lần)
    if not db.query(User).filter(User.email == my_email).first():
        # Tạo User
        my_user = User(
            email=my_email,
            password="123",  # Mật khẩu tạm
            role=UserRole.STUDENT,
            status="active"
        )
        db.add(my_user)
        db.commit()
        db.refresh(my_user)
        
        # Tạo Hồ sơ sinh viên (Bắt buộc phải có để không bị lỗi dashboard)
        my_student = Student(
            userId=my_user.id,
            fullName="Bao Tran (Admin Student)", # Tên hiển thị
            dob=datetime(1998, 7, 9),
            major="Information Technology"
        )
        db.add(my_student)
        db.commit()
        db.refresh(my_student)

        # Tạo Profile chi tiết
        my_profile = StudentProfile(
            studentId=my_student.id,
            cvUrl="https://linkedin.com/in/baotv",
            about="Xin chào, tôi là chủ sở hữu tài khoản này. Đang test hệ thống LabOdc."
        )
        db.add(my_profile)
        db.commit()
        print(f"✅ Đã tạo tài khoản: {my_email} / Pass: 123")

    # ==========================================
    # 2. TẠO DỮ LIỆU MẪU (CÔNG TY & JOB)
    # ==========================================
    company_email = "hr@labodc.com"
    if not db.query(User).filter(User.email == company_email).first():
        # Tạo User Công ty
        comp_user = User(
            email=company_email,
            password="123",
            role=UserRole.COMPANY,
            status="active"
        )
        db.add(comp_user)
        db.commit()
        db.refresh(comp_user)

        # Tạo Profile Công ty
        new_company = Company(
            userId=comp_user.id,
            companyName="LabOdc Tech",
            description="Công ty công nghệ chuyên cung cấp giải pháp tuyển dụng thông minh.",
            website="https://labodc.com"
        )
        db.add(new_company)
        db.commit()
        db.refresh(new_company)

        # Tạo 2 Job mẫu
        jobs = [
            Job(companyId=new_company.id, title="Backend Developer (Python)", description="Phát triển hệ thống API với FastAPI.", location="HCM", status="open"),
            Job(companyId=new_company.id, title="Frontend Developer (Streamlit)", description="Xây dựng giao diện Dashboard.", location="Remote", status="open")
        ]
        db.add_all(jobs)
        db.commit()
        print("✅ Đã tạo Công ty và Job mẫu.")

except Exception as e:
    print(f"❌ Có lỗi xảy ra: {e}")
    db.rollback()
finally:
    db.close()
    print("--- HOÀN TẤT ---")