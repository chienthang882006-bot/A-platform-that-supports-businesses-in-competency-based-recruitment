from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from database import db_session
from models.user_models import User, UserRole
from models.job_models import Job
from models.app_models import Application, Report

admin_bp = Blueprint("admin_router", __name__)


# CHECK ROLE ADMIN (JWT)
def require_admin():
    claims = get_jwt()
    if claims.get("role") != UserRole.ADMIN.value:
        return jsonify({"detail": "Forbidden"}), 403
    return None


# ADMIN DASHBOARD
@admin_bp.route("/admin/home", methods=["GET"])
@jwt_required()  # yêu cầu JWT hợp lệ
def admin_home():
    auth = require_admin()
    if auth:
        return auth

    students = db_session.query(User).filter(
        User.role == UserRole.STUDENT
    ).count()

    companies = db_session.query(User).filter(
        User.role == UserRole.COMPANY
    ).count()

    return jsonify({
        "users": {
            "total": students + companies,  # không tính admin
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


# GET ALL USERS
@admin_bp.route("/admin/users", methods=["GET"])
@jwt_required()
def admin_get_users():
    auth = require_admin()
    if auth:
        return auth

    users = db_session.query(User).all()
    return jsonify([{
        "id": u.id,
        "email": u.email,
        "role": u.role.value,
        "status": u.status,
        "createdAt": u.createdAt.isoformat() if u.createdAt else None
    } for u in users])


# LOCK USER
@admin_bp.route("/admin/users/<int:user_id>/lock", methods=["PUT"])
@jwt_required()
def lock_user(user_id):
    auth = require_admin()
    if auth:
        return auth

    user = db_session.query(User).get(user_id)
    if not user:
        return jsonify({"detail": "User not found"}), 404

    # không cho admin tự khóa chính mình
    if user.id == get_jwt_identity():
        return jsonify({"detail": "Cannot lock yourself"}), 400

    user.status = "locked"
    db_session.commit()
    return jsonify({"message": "User locked"})


# UNLOCK USER
@admin_bp.route("/admin/users/<int:user_id>/unlock", methods=["PUT"])
@jwt_required()
def unlock_user(user_id):
    auth = require_admin()
    if auth:
        return auth

    user = db_session.query(User).get(user_id)
    if not user:
        return jsonify({"detail": "User not found"}), 404

    user.status = "active"
    db_session.commit()
    return jsonify({"message": "User unlocked"})


# GET ALL JOBS
@admin_bp.route("/admin/jobs", methods=["GET"])
@jwt_required()
def admin_get_jobs():
    auth = require_admin()
    if auth:
        return auth

    jobs = db_session.query(Job).all()
    return jsonify([{
        "id": j.id,
        "title": j.title,
        "companyId": j.companyId,
        "status": j.status,
        "maxApplicants": j.maxApplicants
    } for j in jobs])


# CLOSE JOB
@admin_bp.route("/admin/jobs/<int:job_id>/close", methods=["PUT"])
@jwt_required()
def admin_close_job(job_id):
    auth = require_admin()
    if auth:
        return auth

    job = db_session.query(Job).get(job_id)
    if not job:
        return jsonify({"detail": "Job not found"}), 404

    job.status = "CLOSED"
    db_session.commit()
    return jsonify({"message": "Job closed"})


# VIEW JOB APPLICATIONS
@admin_bp.route("/admin/jobs/<int:job_id>/applications", methods=["GET"])
@jwt_required()
def admin_view_applications(job_id):
    auth = require_admin()
    if auth:
        return auth

    apps = db_session.query(Application).filter(
        Application.jobId == job_id
    ).all()

    return jsonify([{
        "applicationId": a.id,
        "studentId": a.studentId,
        "status": a.status.value if hasattr(a.status, "value") else a.status,
        "appliedAt": a.appliedAt.isoformat() if a.appliedAt else None
    } for a in apps])
    
# VIEW REPORTS
@admin_bp.route("/admin/reports", methods=["GET"])
@jwt_required()
def admin_get_reports():
    auth = require_admin()
    if auth:
        return auth

    reports = db_session.query(Report) \
        .order_by(Report.createdAt.desc()) \
        .all()

    return jsonify([
        {
            "id": r.id,
            "companyId": r.companyId,
            "companyName": r.company.companyName if r.company else None,
            "reportType": r.reportType,
            "content": r.content,
            "createdAt": r.createdAt.isoformat() if r.createdAt else None
        } for r in reports
    ])
    
    
@admin_bp.route("/admin/companies/<int:company_id>/reports", methods=["GET"])
@jwt_required()
def admin_get_reports_by_company(company_id):
    auth = require_admin()
    if auth:
        return auth

    reports = db_session.query(Report) \
        .filter(Report.companyId == company_id) \
        .order_by(Report.createdAt.desc()) \
        .all()

    return jsonify([
        {
            "id": r.id,
            "reportType": r.reportType,
            "content": r.content,
            "createdAt": r.createdAt.isoformat()
        } for r in reports
    ])