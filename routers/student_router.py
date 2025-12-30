from flask import Blueprint, request, jsonify
from database import db_session
from datetime import datetime

# Import đầy đủ các models
from models.user_models import Student, StudentProfile
from models.app_models import Application, TestResult, ApplicationStatus
from models.job_models import SkillTest, Job, Question, StudentSkill, Skill

student_bp = Blueprint("student_router", __name__)

# =========================
# 1. LẤY THÔNG TIN STUDENT
# =========================
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
    "skills": [
        {
            "name": ss.skill.name,
            "level": ss.level
        } for ss in student.skills
    ],
    "profile": {
        "cvUrl": student.profile.cvUrl if student.profile else None,
        "about": student.profile.about if student.profile else None,
        "educationLevel": student.profile.educationLevel if student.profile else None,
        "degrees": student.profile.degrees if student.profile else None
    } if student.profile else None
})



# =========================
# 2. CẬP NHẬT HỒ SƠ
# =========================
@student_bp.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.json
    student = db_session.query(Student).filter(Student.id == student_id).first()
    if not student:
        return jsonify({"detail": "Student not found"}), 404

    # ===== 1. students =====
    student.fullName = data.get("fullName", student.fullName)
    student.major = data.get("major", student.major)
    student.cccd = data.get("cccd", student.cccd)

    # ===== 2. student_profiles (CV) =====
    if not student.profile:
        student.profile = StudentProfile(studentId=student.id)

    student.profile.cvUrl = data.get("cvUrl", student.profile.cvUrl)
    student.profile.about = data.get("about", student.profile.about)
    student.profile.educationLevel = data.get("educationLevel", student.profile.educationLevel)
    student.profile.degrees = data.get("degrees", student.profile.degrees)

    # ===== 3. student_skills (KỸ NĂNG) =====
    skills = data.get("skills")  
    # skills = [{ "name": "Python", "level": 4 }, ...]

    if isinstance(skills, list):
        # Xóa kỹ năng cũ
        db_session.query(StudentSkill).filter(
            StudentSkill.studentId == student.id
        ).delete()

        for s in skills:
            skill_name = s.get("name")
            level = s.get("level", 3)
            if not skill_name:
                continue
            # Tìm hoặc tạo skill
            skill = db_session.query(Skill).filter(
                Skill.name == skill_name
            ).first()
            if not skill:
                skill = Skill(name=skill_name, category="general")
                db_session.add(skill)
                db_session.flush()  # lấy skill.id

            db_session.add(StudentSkill(
                studentId=student.id,
                skillId=skill.id,
                level=level
            ))
    db_session.commit()
    return jsonify({
        "message": "Lưu hồ sơ + kỹ năng thành công"
    })


# =========================
# [MỚI] 4. LẤY CHI TIẾT BÀI TEST & CÂU HỎI
# =========================
@student_bp.route("/tests/<int:test_id>", methods=["GET"])
def get_test_details(test_id):
    # Lấy thông tin bài test
    test = db_session.query(SkillTest).filter(SkillTest.id == test_id).first()
    if not test:
        return jsonify({"detail": "Test not found"}), 404

    # Lấy danh sách câu hỏi
    questions = db_session.query(Question).filter(Question.testId == test_id).all()

    question_list = []
    for q in questions:
        question_list.append({
            "id": q.id,
            "content": q.content,
            "options": q.options, # Frontend sẽ parse chuỗi này hiển thị A, B, C, D
            # Lưu ý: Không trả về correctAnswer để bảo mật, Frontend gửi đáp án chọn về server chấm hoặc server trả về điểm sau.
        })
    return jsonify({
        "id": test.id,
        "jobId": test.jobId,
        "testName": test.testName,
        "duration": test.duration,
        "questions": question_list
    })


@student_bp.route("/tests/<int:test_id>/submit", methods=["POST"])
def submit_test(test_id):
    data = request.json
    student_id = data.get("studentId")
    if not student_id:
        return jsonify({"detail": "studentId required"}), 400
    test = db_session.query(SkillTest).filter(SkillTest.id == test_id).first()
    if not test:
        return jsonify({"detail": "Test not found"}), 404
    # Tạo TestResult (flush để lấy id nếu cần)
    tr = TestResult(
        testId=test_id,
        studentId=student_id,
        score=data.get("score", 0)
    )
    db_session.add(tr)
    db_session.flush()  # ensure tr.id is populated
    # Tìm Application của student cho job này (không phụ thuộc trạng thái để tránh mismatch enum)
    app_query = db_session.query(Application).filter(
        Application.jobId == test.jobId,
        Application.studentId == student_id
    ).order_by(Application.appliedAt.desc())
    app_rec = app_query.first()
    if app_rec:
        try:
            app_rec.status = ApplicationStatus.PENDING
        except Exception:
            # nếu status lưu dạng string, set trực tiếp
            app_rec.status = "PENDING"
    db_session.commit()
    return jsonify({
        "message": "Hoàn thành bài test & hồ sơ đã được gửi",
        "testResultId": tr.id,
        "applicationUpdated": bool(app_rec)
    }), 200


# =========================
# 6. XEM DANH SÁCH BÀI TEST (GIỮ NGUYÊN)
# =========================
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


@student_bp.route("/students/<int:student_id>/tests", methods=["GET"])
def get_done_tests(student_id):
    results = db_session.query(TestResult).filter(
        TestResult.studentId == student_id
    ).all()
    out = []
    for r in results:
        submitted_at = None
        # cố gắng lấy trường createdAt / submittedAt nếu model có
        if hasattr(r, "createdAt") and r.createdAt:
            submitted_at = r.createdAt.isoformat()
        elif hasattr(r, "submittedAt") and r.submittedAt:
            submitted_at = r.submittedAt.isoformat()
        out.append({
            "testId": r.testId,
            "testResultId": getattr(r, "id", None),
            "score": getattr(r, "score", None),
            "submittedAt": submitted_at
        })
    return jsonify(out), 200

