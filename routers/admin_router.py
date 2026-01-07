from flask import Blueprint, jsonify, request
from database import db_session
from models.user_models import User, UserRole
from models.job_models import Job
from models.app_models import Application

admin_bp = Blueprint("admin_router", __name__)

@admin_bp.route("/admin/home", methods=["GET"])
def admin_home():
    students = db_session.query(User).filter(
        User.role == UserRole.STUDENT.value
    ).count()

    companies = db_session.query(User).filter(
        User.role == UserRole.COMPANY.value
    ).count()

    return jsonify({
        "users": {
            "total": students + companies,   # ✅ KHÔNG tính admin
            "students": students,
            "companies": companies
        },
        "jobs": {
            "total": db_session.query(Job).count(),
            "open": db_session.query(Job).filter(Job.status != "CLOSED").count(),
            "closed": db_session.query(Job).filter(Job.status == "CLOSED").count()
        },
        "applications": db_session.query(Application).count()
    })


@admin_bp.route("/admin/users", methods=["GET"])
def admin_get_users():
    users = db_session.query(User).all()
    return jsonify([{
        "id": u.id,
        "email": u.email,
        "role": u.role.value,
        "status": u.status,
        "createdAt": u.createdAt.isoformat() if u.createdAt else None
    } for u in users])


@admin_bp.route("/admin/users/<int:user_id>/lock", methods=["PUT"])
def lock_user(user_id):
    user = db_session.query(User).get(user_id)
    if not user:
        return jsonify({"detail": "User not found"}), 404
    user.status = "locked"
    db_session.commit()
    return jsonify({"message": "User locked"})


@admin_bp.route("/admin/users/<int:user_id>/unlock", methods=["PUT"])
def unlock_user(user_id):
    user = db_session.query(User).get(user_id)
    if not user:
        return jsonify({"detail": "User not found"}), 404
    user.status = "active"
    db_session.commit()
    return jsonify({"message": "User unlocked"})


@admin_bp.route("/admin/jobs", methods=["GET"])
def admin_get_jobs():
    jobs = db_session.query(Job).all()
    return jsonify([{
        "id": j.id,
        "title": j.title,
        "companyId": j.companyId,
        "status": j.status,
        "maxApplicants": j.maxApplicants
    } for j in jobs])


@admin_bp.route("/admin/jobs/<int:job_id>/close", methods=["PUT"])
def admin_close_job(job_id):
    job = db_session.query(Job).get(job_id)
    if not job:
        return jsonify({"detail": "Job not found"}), 404
    job.status = "CLOSED"
    db_session.commit()
    return jsonify({"message": "Job closed"})


@admin_bp.route("/admin/jobs/<int:job_id>/applications", methods=["GET"])
def admin_view_applications(job_id):
    apps = db_session.query(Application).filter(Application.jobId == job_id).all()
    return jsonify([{
        "applicationId": a.id,
        "studentId": a.studentId,
        "status": a.status.value if hasattr(a.status, "value") else a.status,
        "appliedAt": a.appliedAt.isoformat() if a.appliedAt else None
    } for a in apps])
