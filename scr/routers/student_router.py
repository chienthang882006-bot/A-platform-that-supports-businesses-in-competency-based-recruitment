from flask import Blueprint, request, jsonify
from scr.database import db_session
from models.user_models import Student, StudentProfile
from models.app_models import Application, TestResult
from models.job_models import SkillTest

student_bp = Blueprint("student_router", __name__)

# 1. Lấy thông tin student theo userId
@student_bp.route("/students/user/<int:user_id>", methods=["GET"])
def get_student_by_user(user_id):
    student = db_session.query(Student).filter(Student.userId == user_id).first()
    if not student:
        return jsonify({"detail": "Student not found"}), 404

    return jsonify({
        "id": student.id,
        "userId": student.userId,
        "fullName": student.fullName,
        "dob": student.dob.isoformat() if student.dob else None,
        "major": student.major,
        "profile": {
            "cvUrl": student.profile.cvUrl if student.profile else None,
            "about": student.profile.about if student.profile else None,
            "educationLevel": student.profile.educationLevel if student.profile else None,
            "degrees": student.profile.degrees if student.profile else None
        } if student.profile else None
    })


# 2. Cập nhật hồ sơ sinh viên
@student_bp.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.json
    student = db_session.query(Student).filter(Student.id == student_id).first()
    if not student:
        return jsonify({"detail": "Student not found"}), 404

    student.fullName = data.get("fullName", student.fullName)
    student.major = data.get("major", student.major)
    student.cccd = data.get("cccd", student.cccd)

    # Cập nhật / tạo profile
    if not student.profile:
        student.profile = StudentProfile(studentId=student.id)

    student.profile.cvUrl = data.get("cvUrl", student.profile.cvUrl)
    student.profile.about = data.get("about", student.profile.about)
    student.profile.educationLevel = data.get("educationLevel", student.profile.educationLevel)
    student.profile.degrees = data.get("degrees", student.profile.degrees)

    db_session.commit()
    return jsonify({"message": "Cập nhật hồ sơ thành công"})

# 3. Student nộp bài test
@student_bp.route("/tests/<int:test_id>/submit", methods=["POST"])
def submit_test(test_id):
    data = request.json

    student_id = data.get("studentId")
    score = data.get("score", 0)

    # kiểm tra test tồn tại
    test = db_session.query(SkillTest).filter(SkillTest.id == test_id).first()
    if not test:
        return jsonify({"detail": "Test not found"}), 404

    result = TestResult(
        testId=test_id,
        studentId=student_id,
        score=score
    )

    db_session.add(result)
    db_session.commit()

    return jsonify({
        "message": "Nộp bài test thành công",
        "score": score
    }), 201


# 4. Student xem danh sách bài test theo job
@student_bp.route("/jobs/<int:job_id>/tests", methods=["GET"])
def get_tests_by_job(job_id):
    tests = db_session.query(SkillTest).filter(
        SkillTest.jobId == job_id
    ).all()

    return jsonify([
        {
            "id": t.id,
            "testName": t.testName,
            "duration": t.duration,
            "totalScore": t.totalScore
        }
        for t in tests
    ])
