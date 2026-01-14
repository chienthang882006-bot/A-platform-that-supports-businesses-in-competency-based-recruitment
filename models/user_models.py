# models/user_models.py
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime,
    Enum, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from .base import Base


# =========================
# ENUM
# =========================
class UserRole(enum.Enum):
    STUDENT = "student"
    COMPANY = "company"
    ADMIN = "admin"


# =========================
# USER
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    status = Column(String, default="active")
    createdAt = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="user", uselist=False)
    company = relationship("Company", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")


# =========================
# STUDENT
# =========================
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), unique=True)

    fullName = Column(String)
    dob = Column(DateTime)
    cccd = Column(String)
    major = Column(String)

    user = relationship("User", back_populates="student")
    profile = relationship(
        "StudentProfile",
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan"
    )
    skills = relationship("StudentSkill", back_populates="student")
    applications = relationship("Application", back_populates="student")
    test_results = relationship("TestResult", back_populates="student")


# =========================
# STUDENT PROFILE
# =========================
class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    studentId = Column(Integer, ForeignKey("students.id"), unique=True)

    cvUrl = Column(String)
    portfolioUrl = Column(String)
    educationLevel = Column(String)
    degrees = Column(Text)
    about = Column(Text)
    updatedAt = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    student = relationship("Student", back_populates="profile")


# =========================
# COMPANY
# =========================
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), unique=True)

    companyName = Column(String(255), nullable=False)

    description = Column(Text)
    website = Column(String(255))
    address = Column(String(255))
    industry = Column(String(100))
    size = Column(String(50))
    logoUrl = Column(String(255))

    user = relationship("User", back_populates="company")
    jobs = relationship("Job", back_populates="company")
    reports = relationship("Report", back_populates="company")

    profile = relationship(
        "CompanyProfile",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan"
    )


# =========================
# COMPANY PROFILE
# =========================
class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True)
    companyId = Column(
        Integer,
        ForeignKey("companies.id"),
        unique=True
    )

    description = Column(Text)
    address = Column(String(255))
    website = Column(String(255))
    size = Column(String(50))
    industry = Column(String(100))
    logoUrl = Column(String(255))

    company = relationship("Company", back_populates="profile")
