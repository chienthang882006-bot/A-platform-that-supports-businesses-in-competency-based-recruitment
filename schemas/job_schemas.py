from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from typing import List

class QuestionCreate(BaseModel):
    content: str
    options: str
    correctAnswer: str

class TestCreate(BaseModel):
    testName: str
    duration: int
    questions: List[QuestionCreate]

class JobBase(BaseModel):
    title: str
    description: str # Text field
    location: Optional[str] = None
    status: str = "open"

class JobCreate(JobBase):
    companyId: int

class JobResponse(JobBase):
    id: int
    companyId: int
    createdAt: datetime
    updatedAt: datetime
    class Config:
        from_attributes = True