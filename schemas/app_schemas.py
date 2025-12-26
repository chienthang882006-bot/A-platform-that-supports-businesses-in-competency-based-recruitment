from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- APPLICATION ---
class ApplicationCreate(BaseModel):
    jobId: int
    studentId: int
    status: str = "pending" # pending, interview, offered...

class ApplicationResponse(ApplicationCreate):
    id: int
    appliedAt: datetime
    updatedAt: datetime
    class Config:
        from_attributes = True

# --- INTERVIEW ---
class InterviewCreate(BaseModel):
    applicationId: int
    interviewDate: datetime
    interviewType: str
    status: str = "scheduled"

class InterviewResponse(InterviewCreate):
    id: int
    class Config:
        from_attributes = True

# --- OFFER ---
class OfferCreate(BaseModel):
    applicationId: int
    offerDetail: str # Text field (Long text)
    status: str = "pending"

class OfferResponse(OfferCreate):
    id: int
    class Config:
        from_attributes = True