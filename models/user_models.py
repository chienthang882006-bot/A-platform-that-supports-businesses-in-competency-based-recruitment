import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class UserRole(enum.Enum):
    STUDENT = "student"
    COMPANY = "company"
    ADMIN = "admin"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    status = Column(String, default="active")
    createdAt = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="user", uselist=False)
    company = relationship("Company", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    isRead = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="notifications")

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey('users.id'), unique=True)
    
    # --- CÁC TRƯỜNG MỚI ---
    fullName = Column(String)
    dob = Column(DateTime)          # Ngày sinh
    cccd = Column(String)           # Căn cước công dân
    major = Column(String)          # Chuyên ngành
    
    user = relationship("User", back_populates="student")
    profile = relationship("StudentProfile", back_populates="student", uselist=False)
    skills = relationship("StudentSkill", back_populates="student")
    applications = relationship("Application", back_populates="student")
    test_results = relationship("TestResult", back_populates="student")

class StudentProfile(Base):
    __tablename__ = 'student_profiles'
    id = Column(Integer, primary_key=True, index=True)
    studentId = Column(Integer, ForeignKey('students.id'), unique=True)
    cvUrl = Column(String)
    portfolioUrl = Column(String)
    
    # --- CÁC TRƯỜNG MỚI ---
    educationLevel = Column(String) # Ví dụ: Đại học, Cao đẳng
    degrees = Column(Text)          # Danh sách bằng cấp, chứng chỉ
    about = Column(Text)            # Giới thiệu bản thân
    
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    student = relationship("Student", back_populates="profile")

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey('users.id'), unique=True)
    companyName = Column(String)
    description = Column(Text) 
    website = Column(String)

    user = relationship("User", back_populates="company")
    jobs = relationship("Job", back_populates="company")
    reports = relationship("Report", back_populates="company")