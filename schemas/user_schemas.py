from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- BASE USER ---
class UserBase(BaseModel):
    email: str
    role: str = "student"
    status: str = "active"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    createdAt: datetime
    class Config:
        from_attributes = True
        use_enum_values = True

# --- STUDENT ---
class StudentProfileBase(BaseModel):
    cvUrl: Optional[str] = None
    portfolioUrl: Optional[str] = None
    about: Optional[str] = None
    educationLevel: Optional[str] = None # Mới
    degrees: Optional[str] = None        # Mới

class StudentBase(BaseModel):
    fullName: str
    dob: Optional[datetime] = None
    cccd: Optional[str] = None           # Mới
    major: Optional[str] = None

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel): # Schema dùng để Update
    fullName: str
    dob: Optional[datetime] = None
    cccd: Optional[str] = None
    major: Optional[str] = None
    # Profile info gộp vào đây để update 1 lần cho tiện
    educationLevel: Optional[str] = None
    degrees: Optional[str] = None
    about: Optional[str] = None

class StudentResponse(StudentBase):
    id: int
    userId: int
    profile: Optional[StudentProfileBase] = None
    class Config:
        from_attributes = True

# --- COMPANY ---
class CompanyBase(BaseModel):
    companyName: str
    description: Optional[str] = None
    website: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: int
    userId: int
    class Config:
        from_attributes = True
class NotificationResponse(BaseModel):
    id: int
    content: str
    isRead: bool
    createdAt: datetime
    class Config:
        from_attributes = True 