from flask import Blueprint, request, jsonify
from database import db_session
from datetime import datetime

# Import đầy đủ các models cần thiết
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
            {"name": ss.skill.name, "level": ss.level} for ss in student.skills
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

    # Update bảng students
    if "fullName" in data: student.fullName = data["fullName"]
    if "major" in data: student.major = data["major"]
    if "cccd" in data: student.cccd = data["cccd"]

    # Update bảng student_profiles
    if not student.profile:
        student.profile = StudentProfile(studentId=student.id)
    if "cvUrl" in data: student.profile.cvUrl = data["cvUrl"]
    if "about" in data: student.profile.about = data["about"]
    if "educationLevel" in data: student.profile.educationLevel = data["educationLevel"]
    if "degrees" in data: student.profile.degrees = data["degrees"]
    if "portfolioUrl" in data: student.profile.portfolioUrl = data["portfolioUrl"]

    # Update kỹ năng
    skills = data.get("skills")
    if isinstance(skills, list):
        db_session.query(StudentSkill).filter(StudentSkill.studentId == student.id).delete()
        for s in skills:
            skill_name = s.get("name")
            level = s.get("level", 3)
            if not skill_name: continue
            
            skill = db_session.query(Skill).filter(Skill.name == skill_name).first()
            if not skill:
                skill = Skill(name=skill_name, category="general")
                db_session.add(skill)
                db_session.flush()

            db_session.add(StudentSkill(studentId=student.id, skillId=skill.id, level=level))
            
    db_session.commit()
    return jsonify({"message": "Lưu hồ sơ thành công"})


# =========================
# 3. LẤY CHI TIẾT BÀI TEST & CÂU HỎI
# =========================
@student_bp.route("/tests/<int:test_id>", methods=["GET"])
def get_test_details(test_id):
    test = db_session.query(SkillTest).filter(SkillTest.id == test_id).first()
    if not test:
        return jsonify({"detail": "Test not found"}), 404

    questions = db_session.query(Question).filter(Question.testId == test_id).all()
    question_list = [{
        "id": q.id,
        "content": q.content,
        "options": q.options
    } for q in questions]

    return jsonify({
        "id": test.id,
        "jobId": test.jobId,
        "testName": test.testName,
        "duration": test.duration,
        "questions": question_list
    })


# =========================
# 4. NỘP BÀI TEST
# =========================
@student_bp.route("/tests/<int:test_id>/submit", methods=["POST"])
def submit_test(test_id):
    data = request.json
    student_id = data.get("studentId")
    if not student_id:
        return jsonify({"detail": "studentId required"}), 400
        
    test = db_session.query(SkillTest).filter(SkillTest.id == test_id).first()
    if not test:
        return jsonify({"detail": "Test not found"}), 404

    # Lưu kết quả
    tr = TestResult(
        testId=test_id,
        studentId=student_id,
        score=data.get("score", 0)
    )
    db_session.add(tr)
    
    # Cập nhật trạng thái Application -> PENDING (Đã test xong)
    app_rec = db_session.query(Application).filter(
        Application.jobId == test.jobId,
        Application.studentId == student_id
    ).first()
    
    if app_rec:
        app_rec.status = ApplicationStatus.PENDING 
        
    db_session.commit()
    return jsonify({"message": "Nộp bài thành công", "testResultId": tr.id}), 200


# =========================
# 5. LẤY DANH SÁCH CÁC BÀI TEST ĐÃ LÀM (BỔ SUNG QUAN TRỌNG)
# (App.py gọi hàm này ở trang Home để biết bài nào đã làm rồi)
# =========================
@student_bp.route("/students/<int:student_id>/tests", methods=["GET"])
def get_student_done_tests(student_id):
    results = db_session.query(TestResult).filter(
        TestResult.studentId == student_id
    ).all()
    
    return jsonify([
        {
            "testId": r.testId,
            "score": r.score,
            "testResultId": r.id
        } for r in results
    ])


# =========================
# 6. LẤY DANH SÁCH ỨNG TUYỂN (KÈM TRẠNG THÁI BÀI TEST)
# =========================
@student_bp.route("/students/<int:student_id>/applications", methods=["GET"])
def get_student_applications(student_id):
    # Lấy danh sách ứng tuyển
    apps = db_session.query(Application).filter(
        Application.studentId == student_id
    ).order_by(Application.appliedAt.desc()).all()

    result = []
    for app in apps:
        job = app.job
        if not job: continue
        
        company = job.company
        
        # --- ĐOẠN MỚI CẦN THÊM VÀO ---
        # 1. Kiểm tra Job có bài test không?
        test = db_session.query(SkillTest).filter(SkillTest.jobId == job.id).first()
        has_test = bool(test)
        test_id = test.id if test else None
        
        # 2. Kiểm tra Sinh viên đã làm chưa?
        test_status = "not_required"
        if has_test:
            prev_result = db_session.query(TestResult).filter(
                TestResult.studentId == student_id,
                TestResult.testId == test.id
            ).first()
            test_status = "done" if prev_result else "pending"
        # -----------------------------

        # Xử lý status an toàn
        status_val = app.status.value if hasattr(app.status, 'value') else str(app.status)

        result.append({
            "id": app.id,
            "jobId": job.id,
            "jobTitle": job.title,
            "companyName": company.companyName if company else "N/A",
            "logoUrl": company.profile.logoUrl if (company and company.profile) else None,
            "status": status_val,
            "appliedAt": app.appliedAt.strftime("%d/%m/%Y"),
            # Trả thêm 3 trường này về cho Frontend dùng
            "hasTest": has_test,     
            "testId": test_id,
            "testStatus": test_status
        })
    
    return jsonify(result)