from flask import Blueprint, request, jsonify
from scr.database import db_session
from models import Job, Company, Application, ApplicationStatus
from models.job_models import Job, SkillTest
from models.user_models import Company, Student
from models.app_models import Application, ApplicationStatus, Evaluation, TestResult


company_bp = Blueprint("company_router", __name__)

# =========================
# GET COMPANY BY USER
# =========================
@company_bp.route("/companies/user/<int:user_id>", methods=["GET"])
def get_company_by_user(user_id):
    company = db_session.query(Company).filter(
        Company.userId == user_id
    ).first()

    if not company:
        return jsonify({"detail": "Company not found"}), 404

    return jsonify({
        "id": company.id,
        "companyName": company.companyName
    })


# =========================
# CREATE JOB
# =========================
@company_bp.route("/jobs/", methods=["POST"])
def create_job():
    data = request.json

    new_job = Job(
        companyId=data["companyId"],
        title=data["title"],
        description=data["description"],
        location=data.get("location"),
        status=data.get("status", "open")
    )

    db_session.add(new_job)
    db_session.commit()
    db_session.refresh(new_job)

    return jsonify({
        "id": new_job.id,
        "title": new_job.title
    }), 201


# =========================
# CREATE SKILL TEST FOR JOB
# =========================
@company_bp.route("/jobs/<int:job_id>/test", methods=["POST"])
def create_skill_test(job_id):
    data = request.json

    test = SkillTest(
        jobId=job_id,
        testName=data["testName"],
        duration=data["duration"],
        totalScore=data["totalScore"]
    )

    db_session.add(test)
    db_session.commit()

    return jsonify({
        "id": test.id,
        "testName": test.testName
    }), 201


# =========================
# VIEW APPLICATIONS BY JOB
# =========================
@company_bp.route("/jobs/<int:job_id>/applications", methods=["GET"])
def get_applications_by_job(job_id):
    apps = db_session.query(Application).filter(
        Application.jobId == job_id
    ).all()

    result = []
    for a in apps:
        student = a.student
        result.append({
            "studentName": student.fullName,
            "status": a.status.value,
            "cvUrl": student.profile.cvUrl if student.profile else None
        })

    return jsonify(result)


# =========================
# VIEW TEST RESULTS BY JOB
# =========================
@company_bp.route("/jobs/<int:job_id>/test-results", methods=["GET"])
def view_test_results(job_id):
    results = db_session.query(
        TestResult, Student, SkillTest
    ).join(
        SkillTest, TestResult.testId == SkillTest.id
    ).join(
        Student, TestResult.studentId == Student.id
    ).filter(
        SkillTest.jobId == job_id
    ).all()

    response = []
    for r, s, t in results:
        response.append({
            "studentId": s.id,
            "studentName": s.fullName,
            "testName": t.testName,
            "score": r.score
        })

    return jsonify(response)


# =========================
# EVALUATE APPLICATION
# =========================
@company_bp.route("/applications/<int:app_id>/evaluate", methods=["POST"])
def evaluate_application(app_id):
    data = request.json

    evaluation = Evaluation(
        applicationId=app_id,
        skillScore=data.get("skillScore"),
        peerReview=data.get("peerReview"),
        improvement=data.get("improvement")
    )

    db_session.add(evaluation)

    # update application status
    app = db_session.query(Application).filter(Application.id == app_id).first()
    if app:
        app.status = ApplicationStatus.INTERVIEW

    db_session.commit()

    return jsonify({"message": "Đã đánh giá ứng viên"}), 201

