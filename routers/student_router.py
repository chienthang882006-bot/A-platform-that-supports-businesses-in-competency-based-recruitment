import json
from datetime import datetime
from pprint import pp
from flask import Blueprint, app, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from database import db_session
from models.user_models import Company, Student, StudentProfile, UserRole
from models.app_models import Application, Report, TestResult, ApplicationStatus
from models.job_models import SkillTest, Job, Question, StudentSkill, Skill

student_bp = Blueprint("student_router", __name__)

# AUTH & HELPERS 
def require_student():
    claims = get_jwt()
    if claims.get("role") != "student":
        return jsonify({"detail": "Forbidden"}), 403
    return None

def get_current_student():
    user_id = int(get_jwt_identity())
    return db_session.query(Student).filter(Student.userId == user_id).first()


# 1. LẤY THÔNG TIN STUDENT
@student_bp.route("/students/user/<int:user_id>", methods=["GET"])
@jwt_required()
def get_student_by_user(user_id):
    auth = require_student()
    if auth:
        return auth

    student = get_current_student()
    if not student or student.userId != user_id:
        return jsonify({"detail": "Forbidden"}), 403

    return jsonify({
        "id": student.id,
        "userId": student.userId,
        "fullName": student.fullName,
        "cccd": student.cccd,
        "dob": student.dob.isoformat() if student.dob is not None else None,
        "major": student.major,
        "skills": [
            {"name": ss.skill.name, "level": ss.level} for ss in student.skills
        ],
        "profile": {
            "cvUrl": student.profile.cvUrl if student.profile else None,
            "about": student.profile.about if student.profile else None,
            "educationLevel": student.profile.educationLevel if student.profile else None,
            "degrees": student.profile.degrees if student.profile else None,
            "portfolioUrl": student.profile.portfolioUrl if student.profile else None
        } if student.profile else None
    })


# 2. BẮT ĐẦU LÀM BÀI TEST
@student_bp.route("/tests/start", methods=["POST"])
@jwt_required()
def start_test_session():
    auth = require_student()
    if auth:
        return auth

    student = get_current_student()
    job_id = request.json.get("jobId")

    job = db_session.query(Job).filter(Job.id == job_id).first()
    if not job:
        return jsonify({"detail": "Job not found"}), 404

    test = db_session.query(SkillTest).filter(SkillTest.jobId == job_id).first()
    if not test:
        return jsonify({"detail": "Job does not have a test"}), 404

    app = db_session.query(Application).filter(
        Application.studentId == student.id,
        Application.jobId == job_id
    ).first()

    if not app:
        db_session.add(Application(
            studentId=student.id,
            jobId=job_id,
            status=ApplicationStatus.TESTING
        ))
        db_session.commit()

    return jsonify({"testId": test.id, "message": "Ready to test"}), 200


# 3. CẬP NHẬT HỒ SƠ STUDENT
@student_bp.route("/students/<int:student_id>", methods=["PUT"])
@jwt_required()
def update_student(student_id):
    auth = require_student()
    if auth:
        return auth

    student = get_current_student()
    if not student or student.id != student_id:
        return jsonify({"detail": "Forbidden"}), 403

    data = request.json

    if "fullName" in data:
        student.fullName = data["fullName"]
    if "major" in data:
        student.major = data["major"]
    if "cccd" in data:
        student.cccd = data["cccd"]
    if "dob" in data and data["dob"]:
        try:
            # Chuyển chuỗi '2000-01-01' thành đối tượng datetime (keeps time component for DB column)
            student.dob = datetime.strptime(data["dob"], "%Y-%m-%d")
        except ValueError:
            pass # Bỏ qua nếu định dạng ngày sai
    if not student.profile:
        student.profile = StudentProfile(studentId=student.id)

    for field in ["cvUrl", "about", "educationLevel", "degrees", "portfolioUrl"]:
        if field in data:
            setattr(student.profile, field, data[field])

    skills = data.get("skills")
    if isinstance(skills, list):
        db_session.query(StudentSkill).filter(
            StudentSkill.studentId == student.id
        ).delete()

        for s in skills:
            name = s.get("name")
            level = s.get("level", 3)
            if not name:
                continue

            skill = db_session.query(Skill).filter(Skill.name == name).first()
            if not skill:
                skill = Skill(name=name, category="general")
                db_session.add(skill)
                db_session.flush()

            db_session.add(StudentSkill(
                studentId=student.id,
                skillId=skill.id,
                level=level
            ))

    db_session.commit()
    return jsonify({"message": "Lưu hồ sơ thành công"})


# 4. LẤY CHI TIẾT BÀI TEST
@student_bp.route("/tests/<int:test_id>", methods=["GET"])
@jwt_required()
def get_test_details(test_id):
    auth = require_student()
    if auth:
        return auth

    test = db_session.query(SkillTest).filter(SkillTest.id == test_id).first()
    if not test:
        return jsonify({"detail": "Test not found"}), 404

    questions = db_session.query(Question).filter(
        Question.testId == test_id
    ).all()

    return jsonify({
        "id": test.id,
        "jobId": test.jobId,
        "testName": test.testName,
        "duration": test.duration,
        "questions": [{
            "id": q.id,
            "content": q.content,
            "options": q.options
        } for q in questions]
    })


# 5. NỘP BÀI TEST
@student_bp.route("/tests/<int:test_id>/submit", methods=["POST"])
@jwt_required()
def submit_test(test_id):
    auth = require_student()
    if auth:
        return auth

    student = get_current_student()
    data = request.json or {}

    test = db_session.query(SkillTest).filter(SkillTest.id == test_id).first()
    if not test:
        return jsonify({"detail": "Test not found"}), 404

    # 1) Lưu kết quả test
    tr = TestResult(
        testId=test_id,
        studentId=student.id,
        score=data.get("score", 0),
        answers=json.dumps(data.get("answers", []))
    )
    db_session.add(tr)

    # 2) Tạo / cập nhật Application => PENDING
    app = db_session.query(Application).filter(
        Application.jobId == test.jobId,
        Application.studentId == student.id
    ).first()

    if not app:
        app = Application(
            studentId=student.id,
            jobId=test.jobId,
            status=ApplicationStatus.PENDING
        )
        db_session.add(app)
    else:
        app.status = ApplicationStatus.PENDING

    db_session.commit()
    return jsonify({"message": "Submitted", "applicationStatus": "PENDING"}), 200




# 6. DANH SÁCH ỨNG TUYỂN
@student_bp.route("/students/<int:student_id>/applications", methods=["GET"])
@jwt_required()
def get_student_applications(student_id):
    auth = require_student()
    if auth:
        return auth

    student = get_current_student()
    if student.id != student_id:
        return jsonify({"detail": "Forbidden"}), 403

    apps = db_session.query(Application).filter(
        Application.studentId == student_id
    ).order_by(Application.appliedAt.desc()).all()

    result = []
    for app in apps:
        job = app.job
        if not job:
            continue

        test = db_session.query(SkillTest).filter(
            SkillTest.jobId == job.id
        ).first()

        has_test = bool(test)
        test_status = "not_required"
        if has_test:
            done = db_session.query(TestResult).filter(
                TestResult.studentId == student_id,
                TestResult.testId == test.id
            ).first()
            test_status = "done" if done else "pending"

        result.append({
            "id": app.id,
            "jobId": job.id,
            "jobTitle": job.title,
            "companyName": job.company.companyName if job.company else "N/A",
            "logoUrl": job.company.profile.logoUrl if job.company and job.company.profile else None,
            "status": app.status.value if hasattr(app.status, "value") else str(app.status),
            "appliedAt": app.appliedAt.strftime("%d/%m/%Y"),
            "hasTest": has_test,
            "testId": test.id if test else None,
            "testStatus": test_status
        })

    return jsonify(result)


@student_bp.route("/student/reports", methods=["POST"])
@jwt_required()
def student_report_company():
    auth = require_student()
    if auth:
        return auth

    data = request.json or {}
    company_id = data.get("companyId")

    student = get_current_student()

    # ✅ KHÔNG CHO REPORT NHIỀU LẦN
    existed = db_session.query(Report).filter(
        Report.companyId == company_id,
        Report.studentId == student.id   # 👈 quan trọng
    ).first()

    if existed:
        # 👉 Đã report rồi thì coi như xong
        return jsonify({"message": "Already reported"}), 200

    report = Report(
        companyId=company_id,
        studentId=student.id,   # 👈 gắn student
        reportType=data.get("reportType"),
        content=data.get("content")
    )

    db_session.add(report)
    db_session.commit()

    return jsonify({"message": "Reported"}), 201

