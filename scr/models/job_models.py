from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, index=True)
    companyId = Column(Integer, ForeignKey('companies.id'))
    title = Column(String)
    
    # CẬP NHẬT: Mô tả công việc rất dài, dùng Text
    description = Column(Text) 
    location = Column(String)
    status = Column(String, default="open") # open, closed, draft
    
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="jobs")
    job_skills = relationship("JobSkill", back_populates="job")
    skill_tests = relationship("SkillTest", back_populates="job")
    applications = relationship("Application", back_populates="job")

class Skill(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    category = Column(String)

    student_skills = relationship("StudentSkill", back_populates="skill")
    job_skills = relationship("JobSkill", back_populates="skill")

# Bảng trung gian Student - Skill
class StudentSkill(Base):
    __tablename__ = 'student_skills'
    studentId = Column(Integer, ForeignKey('students.id'), primary_key=True)
    skillId = Column(Integer, ForeignKey('skills.id'), primary_key=True)
    level = Column(Integer) # Ví dụ: 1-5 hoặc 1-10

    student = relationship("Student", back_populates="skills")
    skill = relationship("Skill", back_populates="student_skills")

# Bảng trung gian Job - Skill
class JobSkill(Base):
    __tablename__ = 'job_skills'
    jobId = Column(Integer, ForeignKey('jobs.id'), primary_key=True)
    skillId = Column(Integer, ForeignKey('skills.id'), primary_key=True)
    requiredLevel = Column(Integer)

    job = relationship("Job", back_populates="job_skills")
    skill = relationship("Skill", back_populates="job_skills")

class SkillTest(Base):
    __tablename__ = 'skill_tests'
    id = Column(Integer, primary_key=True, index=True)
    jobId = Column(Integer, ForeignKey('jobs.id'))
    testName = Column(String)
    duration = Column(Integer) # Minutes
    totalScore = Column(Integer)

    job = relationship("Job", back_populates="skill_tests")
    test_results = relationship("TestResult", back_populates="test")