from database import SessionLocal
from models import User, Student, StudentProfile
from datetime import datetime

# 1. Tạo phiên làm việc (Session)
db = SessionLocal()

try:
    print("--- Bắt đầu thêm dữ liệu mẫu ---")

    # 2. Tạo một User mới
    new_user = User(
        email="sinhvien@example.com",
        password="hashed_password_123", # Thực tế nên mã hóa password
        role="student",
        status="active"
    )
    db.add(new_user)
    db.commit() # Lưu User để lấy ID
    db.refresh(new_user) # Cập nhật lại object để lấy ID vừa sinh ra
    print(f"Đã tạo User ID: {new_user.id}")

    # 3. Tạo thông tin Student liên kết với User đó
    new_student = Student(
        userId=new_user.id,
        fullName="Nguyen Van A",
        dob=datetime(2000, 1, 1),
        major="Information Technology"
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    print(f"Đã tạo Student: {new_student.fullName} (ID: {new_student.id})")

    # 4. Tạo Profile cho sinh viên này
    new_profile = StudentProfile(
        studentId=new_student.id,
        cvUrl="https://example.com/cv.pdf",
        about="Sinh viên năm cuối đam mê lập trình Python."
    )
    db.add(new_profile)
    db.commit()
    print("Đã tạo Student Profile thành công!")

    # 5. Truy vấn ngược lại để kiểm tra mối quan hệ
    # Lấy user từ database và xem thông tin student đi kèm
    user_in_db = db.query(User).filter(User.email == "sinhvien@example.com").first()
    print(f"\nKiểm tra dữ liệu lấy ra:")
    print(f"User Email: {user_in_db.email}")
    print(f"Tên sinh viên (qua relationship): {user_in_db.student.fullName}")
    print(f"Ngành học: {user_in_db.student.major}")

except Exception as e:
    print(f"Có lỗi xảy ra: {e}")
    db.rollback() # Hoàn tác nếu lỗi
finally:
    db.close() # Đóng kết nối