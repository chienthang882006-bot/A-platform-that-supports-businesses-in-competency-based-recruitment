from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal
from models import User, Student, Company, UserRole # Import thêm UserRole
from schemas import user_schemas

router = APIRouter(tags=["User Management"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. Lấy danh sách User
@router.get("/users/", response_model=List[user_schemas.UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# 2. Tạo User mới (ĐÃ SỬA LỖI ENUM)
@router.post("/users/", response_model=user_schemas.UserResponse)
def create_user(user: user_schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email này đã tồn tại")
    
    try:
        # Chuyển đổi string (từ frontend) sang Enum (cho database)
        role_enum = UserRole(user.role.lower()) 
    except ValueError:
        # Nếu gửi sai role, mặc định là student
        role_enum = UserRole.STUDENT

    new_user = User(
        email=user.email, 
        password=user.password, 
        role=role_enum, # Lưu bằng Enum
        status=user.status
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 3. API cho Student
@router.post("/students/{user_id}", response_model=user_schemas.StudentResponse)
def create_student_profile(user_id: int, student: user_schemas.StudentCreate, db: Session = Depends(get_db)):
    new_student = Student(userId=user_id, **student.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@router.get("/students/user/{user_id}")
def get_student_by_user_id(user_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.userId == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Chưa có hồ sơ sinh viên")
    return student

# 4. API cho Company
@router.post("/companies/{user_id}", response_model=user_schemas.CompanyResponse)
def create_company_profile(user_id: int, company: user_schemas.CompanyCreate, db: Session = Depends(get_db)):
    new_company = Company(userId=user_id, **company.dict())
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company

@router.get("/companies/user/{user_id}")
def get_company_by_user_id(user_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.userId == user_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Chưa có hồ sơ công ty")
    return company
@router.get("/students/user/{user_id}")
def get_student_by_user_id(user_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.userId == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Chưa có hồ sơ sinh viên")
    return student

@router.get("/companies/user/{user_id}")
def get_company_by_user_id(user_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.userId == user_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Chưa có hồ sơ công ty")
    return company

# --- API MỚI: CẬP NHẬT HỒ SƠ SINH VIÊN ---
@router.put("/students/{student_id}", response_model=user_schemas.StudentResponse)
def update_student_profile(student_id: int, info: user_schemas.StudentUpdate, db: Session = Depends(get_db)):
    # 1. Tìm Student
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # 2. Update thông tin bảng Student
    student.fullName = info.fullName
    student.major = info.major
    student.dob = info.dob
    student.cccd = info.cccd
    
    # 3. Update hoặc Tạo mới bảng StudentProfile
    profile = db.query(StudentProfile).filter(StudentProfile.studentId == student_id).first()
    if not profile:
        profile = StudentProfile(studentId=student_id)
        db.add(profile)
    
    profile.educationLevel = info.educationLevel
    profile.degrees = info.degrees
    profile.about = info.about
    
    db.commit()
    db.refresh(student)
    return student