from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal
from models import Job, Application, Interview, Offer, Student, Company
from schemas import job_schemas, app_schemas

router = APIRouter(tags=["Recruitment Process"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- JOB ---
@router.post("/jobs/", response_model=job_schemas.JobResponse)
def create_job(job: job_schemas.JobCreate, db: Session = Depends(get_db)):
    new_job = Job(**job.dict())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

@router.get("/jobs/", response_model=List[job_schemas.JobResponse])
def get_all_jobs(db: Session = Depends(get_db)):
    # Có thể thêm .order_by(Job.createdAt.desc()) để tin mới nhất lên đầu
    return db.query(Job).all()

@router.get("/jobs/my-jobs/{user_id}")
def get_company_jobs(user_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.userId == user_id).first()
    if not company:
        return []
    jobs = db.query(Job).filter(Job.companyId == company.id).all()
    return jobs

# --- APPLICATION ---
@router.post("/apply/", response_model=app_schemas.ApplicationResponse)
def apply_job(app: app_schemas.ApplicationCreate, db: Session = Depends(get_db)):
    # Kiểm tra xem đã ứng tuyển chưa (Optional)
    exists = db.query(Application).filter(
        Application.studentId == app.studentId, 
        Application.jobId == app.jobId
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Bạn đã ứng tuyển công việc này rồi.")
        
    new_app = Application(**app.dict())
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app

@router.get("/applications/my-applications/{user_id}")
def get_my_applications(user_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.userId == user_id).first()
    if not student:
        return []
        
    apps = db.query(Application).filter(Application.studentId == student.id).all()
    
    result = []
    for app in apps:
        job = db.query(Job).filter(Job.id == app.jobId).first()
        # Xử lý Enum status sang string để frontend dễ đọc
        status_str = app.status.value if hasattr(app.status, 'value') else str(app.status)
        
        result.append({
            "id": app.id,
            "jobTitle": job.title if job else "Job đã bị xóa",
            "companyId": job.companyId if job else 0,
            "status": status_str,
            "appliedAt": app.appliedAt
        })
    return result

# --- INTERVIEW & OFFER ---
@router.post("/interviews/", response_model=app_schemas.InterviewResponse)
def schedule_interview(interview: app_schemas.InterviewCreate, db: Session = Depends(get_db)):
    new_iv = Interview(**interview.dict())
    db.add(new_iv)
    db.commit()
    db.refresh(new_iv)
    return new_iv

@router.post("/offers/", response_model=app_schemas.OfferResponse)
def send_offer(offer: app_schemas.OfferCreate, db: Session = Depends(get_db)):
    new_offer = Offer(**offer.dict())
    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)
    return new_offer