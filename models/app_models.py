import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

# Enum trạng thái ứng tuyển
class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    INTERVIEW = "interview"
    OFFERED = "offered"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True, index=True)
    studentId = Column(Integer, ForeignKey('students.id'))
    jobId = Column(Integer, ForeignKey('jobs.id'))
    
    # Sử dụng Enum hoặc String với default
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    
    appliedAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    interviews = relationship("Interview", back_populates="application")
    evaluation = relationship("Evaluation", back_populates="application", uselist=False)
    offer = relationship("Offer", back_populates="application", uselist=False)

class Interview(Base):
    __tablename__ = 'interviews'
    id = Column(Integer, primary_key=True, index=True)
    applicationId = Column(Integer, ForeignKey('applications.id'))
    interviewDate = Column(DateTime)
    interviewType = Column(String) # Online/Offline/Technical...
    status = Column(String) # Scheduled, Completed, Cancelled

    application = relationship("Application", back_populates="interviews")
    feedbacks = relationship("InterviewFeedback", back_populates="interview")

class InterviewFeedback(Base):
    __tablename__ = 'interview_feedbacks'
    id = Column(Integer, primary_key=True, index=True)
    interviewId = Column(Integer, ForeignKey('interviews.id'))
    
    # CẬP NHẬT: Feedback phỏng vấn thường dài
    feedback = Column(Text) 
    rating = Column(Integer)

    interview = relationship("Interview", back_populates="feedbacks")

class Evaluation(Base):
    __tablename__ = 'evaluations'
    id = Column(Integer, primary_key=True, index=True)
    applicationId = Column(Integer, ForeignKey('applications.id'))
    skillScore = Column(Integer)
    
    # CẬP NHẬT: Nhận xét chi tiết
    peerReview = Column(Text) 
    improvement = Column(Text)

    application = relationship("Application", back_populates="evaluation")

class Offer(Base):
    __tablename__ = 'offers'
    id = Column(Integer, primary_key=True, index=True)
    applicationId = Column(Integer, ForeignKey('applications.id'))
    
    # CẬP NHẬT: Chi tiết offer (lương, thưởng, phúc lợi) rất dài
    offerDetail = Column(Text) 
    status = Column(String) # Pending, Accepted, Declined

    application = relationship("Application", back_populates="offer")

class TestResult(Base):
    __tablename__ = 'test_results'
    id = Column(Integer, primary_key=True, index=True)
    testId = Column(Integer, ForeignKey('skill_tests.id'))
    studentId = Column(Integer, ForeignKey('students.id'))
    score = Column(Integer)
    submittedAt = Column(DateTime, default=datetime.utcnow)

    test = relationship("SkillTest", back_populates="test_results")
    student = relationship("Student", back_populates="test_results")

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True, index=True)
    companyId = Column(Integer, ForeignKey('companies.id'))
    reportType = Column(String)
    content = Column(Text) # Thêm nội dung báo cáo
    createdAt = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="reports")