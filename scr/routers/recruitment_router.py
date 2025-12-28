from flask import Blueprint, request, jsonify
from scr.database import db_session
from models import Job, Application, Student, Company, ApplicationStatus

recruitment_bp = Blueprint('recruitment_router', __name__)

@recruitment_bp.route("/jobs/", methods=["GET"])
def get_all_jobs():
    jobs = db_session.query(Job).all()
    return jsonify([{
        "id": j.id,
        "title": j.title,
        "description": j.description,
        "location": j.location,
        "status": j.status
    } for j in jobs])

@recruitment_bp.route("/apply/", methods=["POST"])
def apply_job():
    data = request.json
    exists = db_session.query(Application).filter(
        Application.studentId == data['studentId'],
        Application.jobId == data['jobId']
    ).first()
    
    if exists:
        return jsonify({"detail": "Bạn đã ứng tuyển công việc này rồi."}), 400
        
    new_app = Application(
        jobId=data['jobId'],
        studentId=data['studentId'],
        status=ApplicationStatus.PENDING
    )
    db_session.add(new_app)
    db_session.commit()
    return jsonify({"id": new_app.id, "status": "pending"})
@recruitment_bp.route("/students/<int:student_id>/applications", methods=["GET"])
def get_student_applications(student_id):
    apps = db_session.query(Application).filter(
        Application.studentId == student_id
    ).all()

    return jsonify([{
        "applicationId": a.id,
        "jobId": a.job.id,
        "jobTitle": a.job.title,
        "status": a.status.value,
        "appliedAt": a.appliedAt.isoformat()
    } for a in apps])
