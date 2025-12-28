import enum
# models/user_models.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Boolean
# Đảm bảo có cả 'Text' và 'Boolean' để không bị lỗi tương tự
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

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey('users.id'), unique=True)
    fullName = Column(String)
    dob = Column(DateTime)
    cccd = Column(String)
    major = Column(String)
    
    user = relationship("User", back_populates="student")
    profile = relationship("StudentProfile", back_populates="student", uselist=False)
    # Sử dụng chuỗi ký tự cho class ở file khác để tránh lỗi vòng lặp import
    skills = relationship("StudentSkill", back_populates="student") 
    applications = relationship("Application", back_populates="student")
    test_results = relationship("TestResult", back_populates="student")

class StudentProfile(Base):
    __tablename__ = 'student_profiles'
    id = Column(Integer, primary_key=True, index=True)
    studentId = Column(Integer, ForeignKey('students.id'), unique=True)
    cvUrl = Column(String)
    portfolioUrl = Column(String)
    educationLevel = Column(String) 
    degrees = Column(Text) # Lỗi NameError xảy ra tại đây
    about = Column(Text)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    student = relationship("Student", back_populates="profile")

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey('users.id'))
    content = Column(Text) # Sử dụng Text ở đây
    isRead = Column(Boolean, default=False) # Sử dụng Boolean ở đây
    createdAt = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")

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