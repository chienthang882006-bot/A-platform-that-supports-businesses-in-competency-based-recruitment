import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import func

# Database & Models
from database import db_session
from models.job_models import Job, SkillTest, Question, JobSkill, Skill
from models.user_models import Company, Student, CompanyProfile
from models.app_models import Application, ApplicationStatus, Evaluation, TestResult, Interview, Notification, InterviewFeedback

company_bp = Blueprint("company_router", __name__)

# =========================
# HELPER FUNCTIONS
# =========================
def safe_int(value, default=0):
    """Chuyển đổi an toàn sang int."""
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def serialize_status(status_obj):
    """Lấy value từ Enum nếu có, hoặc trả về chính nó."""
    return status_obj.value if hasattr(status_obj, 'value') else status_obj

def get_student_cv_url(student):
    """Lấy CV URL an toàn từ student object."""
    if hasattr(student, 'profile') and student.profile:
        return student.profile.cvUrl
    return None

# =========================
# COMPANY & PROFILE ROUTES
# =========================

@company_bp.route("/companies/user/<int:user_id>", methods=["GET"])
def get_company_by_user(user_id):
    company = db_session.query(Company).filter(Company.userId == user_id).first()
    if not company:
        return jsonify({"detail": "Company not found"}), 404
    return jsonify({"id": company.id, "companyName": company.companyName})

@company_bp.route("/companies/user/<int:user_id>/profile", methods=["GET"])
def get_company_profile(user_id):
    company = db_session.query(Company).filter(Company.userId == user_id).first()
    if not company:
        return jsonify({"detail": "Company not found"}), 404

    profile = db_session.query(CompanyProfile).filter(CompanyProfile.companyId == company.id).first()
    
    return jsonify({
        "id": company.id,
        "companyName": company.companyName,
        "description": profile.description if profile else "",
        "website": profile.website if profile else "",
        "address": profile.address if profile else "",
        "industry": profile.industry if profile else "",
        "size": profile.size if profile else "",
        "logoUrl": profile.logoUrl if profile else ""
    })

@company_bp.route("/companies/<int:company_id>/profile", methods=["PUT"])
def update_company_profile(company_id):
    data = request.json
    try:
        company = db_session.query(Company).filter(Company.id == company_id).first()
        if not company:
            return jsonify({"detail": "Company not found"}), 404

        # Update Company Name
        if "companyName" in data:
            company.companyName = data["companyName"]

        # Update or Create Profile
        profile = db_session.query(CompanyProfile).filter(CompanyProfile.companyId == company.id).first()
        if not profile:
            profile = CompanyProfile(companyId=company.id)
            db_session.add(profile)
        
        # Mapping fields
        fields = ["description", "website", "address", "industry", "size", "logoUrl"]
        for field in fields:
            if field in data:
                setattr(profile, field, data[field])

        db_session.commit()
        return jsonify({"message": "Cập nhật hồ sơ công ty thành công"})
    except Exception as e:
        db_session.rollback()
        print(f"Update profile error: {e}")
        return jsonify({"detail": f"Lỗi server: {str(e)}"}), 500

# =========================
# JOB MANAGEMENT ROUTES
# =========================

@company_bp.route("/companies/<int:company_id>/jobs", methods=["GET"])
def get_jobs_by_company(company_id):
    """Lấy danh sách việc làm và đếm số lượng ứng tuyển."""
    jobs = db_session.query(Job).filter(Job.companyId == company_id).all()
    response = []
    
    for job in jobs:
        # Tối ưu: Nếu hệ thống lớn, nên dùng group_by count query ở ngoài vòng lặp
        applied_count = db_session.query(func.count(Application.id)).filter(Application.jobId == job.id).scalar()
        
        response.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "location": job.location,
            "status": job.status,
            "appliedCount": applied_count,
            "maxApplicants": job.maxApplicants
        })
    return jsonify(response)

@company_bp.route("/jobs/<int:job_id>", methods=["GET"])
def get_job_detail(job_id):
    job = db_session.query(Job).filter(Job.id == job_id).first()
    if not job:
        return jsonify({"detail": "Job not found"}), 404
    return jsonify({
        "id": job.id,
        "companyId": job.companyId,
        "title": job.title,
        "description": job.description,
        "location": job.location,
        "status": job.status,
        "maxApplicants": job.maxApplicants
    })

@company_bp.route("/jobs/", methods=["GET"])
def get_all_open_jobs():
    """API cho Student: Lấy job đang mở."""
    jobs = db_session.query(Job).filter(Job.status == "open").order_by(Job.createdAt.desc()).all()
    response = []
    for job in jobs:
        # Check test existence safely
        test = job.skill_tests[0] if job.skill_tests else None
        
        response.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "location": job.location,
            "status": job.status,
            "companyId": job.companyId,
            "maxApplicants": job.maxApplicants,
            "hasTest": bool(test),
            "testId": test.id if test else None
        })
    return jsonify(response)

@company_bp.route("/jobs/", methods=["POST"])
def create_job():
    data = request.json
    try:
        # 1. Tạo Job
        new_job = Job(
            companyId=data["companyId"],
            title=data["title"],
            description=data["description"],
            location=data.get("location"),
            status=data.get("status", "open"),
            maxApplicants=safe_int(data.get("maxApplicants"), 0)
        )
        db_session.add(new_job)
        db_session.flush()  # Có ID ngay để dùng cho bài test

        # 2. Tạo Test (nếu có)
        test_data = data.get("test")
        if test_data:
            new_test = SkillTest(
                jobId=new_job.id,
                testName=test_data.get("testName", f"Test for {new_job.title}"),
                duration=safe_int(test_data.get("duration"), 30),
                totalScore=safe_int(test_data.get("totalScore"), 100)
            )
            db_session.add(new_test)
            db_session.flush()

            # 3. Tạo câu hỏi
            questions_data = test_data.get("questions", [])
            for q in questions_data:
                db_session.add(Question(
                    testId=new_test.id,
                    content=q["content"],
                    options=str(q["options"]),
                    correctAnswer=q["correctAnswer"]
                ))

        db_session.commit()
        return jsonify({"message": "Đã tạo công việc thành công", "job": {"id": new_job.id}}), 201

    except Exception as e:
        db_session.rollback()
        print(f"Error creating job: {e}")
        return jsonify({"detail": f"Lỗi khi tạo job: {str(e)}"}), 500

@company_bp.route("/jobs/<int:job_id>", methods=["PUT"])
def update_job(job_id):
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"detail": "No data provided"}), 400

    job = db_session.query(Job).filter(Job.id == job_id).first()
    if not job:
        return jsonify({"detail": "Job not found"}), 404

    try:
        # 1. Update Basic Info
        if "title" in data: setattr(job, "title", str(data["title"]))
        if "description" in data: setattr(job, "description", str(data["description"]))
        if "location" in data: setattr(job, "location", str(data["location"]))
        if "status" in data: setattr(job, "status", str(data["status"]))
        if "maxApplicants" in data: setattr(job, "maxApplicants", safe_int(data["maxApplicants"]))

        # 2. Update Test Logic
        test_data = data.get("test") or (data if "testName" in data else None)
        
        if test_data:
            # Chuẩn hóa input test về dict
            if not isinstance(test_data, dict):
                 test_data = {"testName": str(test_data)}

            skill_test = db_session.query(SkillTest).filter(SkillTest.jobId == job.id).first()
            
            t_name = str(test_data.get("testName", ""))
            t_duration = safe_int(test_data.get("duration"), 30)
            t_score = safe_int(test_data.get("totalScore"), 100)

            if t_name:
                if not skill_test:
                    skill_test = SkillTest(jobId=job.id, testName=t_name, duration=t_duration, totalScore=t_score)
                    db_session.add(skill_test)
                    db_session.flush()
                else:
                    setattr(skill_test, "testName", t_name)
                    setattr(skill_test, "duration", t_duration)
                    setattr(skill_test, "totalScore", t_score)
                
                # Update Questions (Delete old -> Insert new)
                questions_data = test_data.get("questions")
                if isinstance(questions_data, list):
                    db_session.query(Question).filter(Question.testId == skill_test.id).delete()
                    for q in questions_data:
                        db_session.add(Question(
                            testId=skill_test.id,
                            content=str(q.get("content", "")),
                            options=str(q.get("options", "")),
                            correctAnswer=str(q.get("correctAnswer", ""))
                        ))

        db_session.commit()
        return jsonify({"message": "Cập nhật thành công", "id": job.id})

    except Exception as e:
        db_session.rollback()
        print(f"Update job error: {e}")
        return jsonify({"detail": f"Lỗi cập nhật: {str(e)}"}), 500

# =========================
# TEST MANAGEMENT
# =========================

@company_bp.route("/jobs/<int:job_id>/test", methods=["POST"])
def create_skill_test(job_id):
    data = request.json
    try:
        test = SkillTest(
            jobId=job_id,
            testName=data.get("testName", "Skill Test"),
            duration=safe_int(data.get("duration"), 30),
            totalScore=safe_int(data.get("totalScore"), 100)
        )
        db_session.add(test)
        db_session.flush()

        if "questions" in data and isinstance(data["questions"], list):
            for q in data["questions"]:
                db_session.add(Question(
                    testId=test.id,
                    content=q["content"],
                    options=str(q.get("options", "")),
                    correctAnswer=q["correctAnswer"]
                ))
        
        db_session.commit()
        return jsonify({"id": test.id, "message": "Đã tạo bài test thành công"}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"detail": f"Lỗi tạo bài test: {str(e)}"}), 500

@company_bp.route("/jobs/<int:job_id>/test-results", methods=["GET"])
def view_test_results(job_id):
    results = db_session.query(TestResult, Student, SkillTest)\
        .join(SkillTest, TestResult.testId == SkillTest.id)\
        .join(Student, TestResult.studentId == Student.id)\
        .filter(SkillTest.jobId == job_id).all()
        
    return jsonify([{
        "studentId": s.id,
        "studentName": s.fullName,
        "testName": t.testName,
        "score": r.score,
        "submittedAt": r.submittedAt
    } for r, s, t in results])

# =========================
# APPLICATION & EVALUATION
# =========================

@company_bp.route("/companies/<int:company_id>/applications", methods=["GET"])
def get_all_applications_for_company(company_id):
    """Dashboard: Xem toàn bộ đơn ứng tuyển của công ty."""
    apps = db_session.query(Application).join(Job).filter(Job.companyId == company_id).all()
    response = []
    
    for app in apps:
        test_score = "N/A"
        # Logic lấy điểm test
        if app.job.skill_tests:
            test = app.job.skill_tests[0]
            tr = db_session.query(TestResult).filter(
                TestResult.studentId == app.student.id,
                TestResult.testId == test.id
            ).first()
            if tr: test_score = tr.score

        response.append({
            "applicationId": app.id,
            "studentName": app.student.fullName,
            "jobTitle": app.job.title,
            "appliedAt": app.appliedAt,
            "status": serialize_status(app.status),
            "testScore": test_score,
            "cvUrl": get_student_cv_url(app.student)
        })
    return jsonify(response)

@company_bp.route("/jobs/<int:job_id>/applications", methods=["GET"])
def get_applications_by_job(job_id):
    apps = db_session.query(Application).filter(Application.jobId == job_id).all()
    return jsonify([{
        "applicationId": app.id,
        "studentName": app.student.fullName,
        "status": serialize_status(app.status),
        "cvUrl": get_student_cv_url(app.student)
    } for app in apps])

@company_bp.route("/applications/<int:app_id>/test-detail", methods=["GET"])
def get_application_test_detail(app_id):
    app = db_session.query(Application).filter(Application.id == app_id).first()
    if not app: return jsonify({"detail": "App not found"}), 404

    # Lấy bài test đầu tiên của job
    test = app.job.skill_tests[0] if app.job.skill_tests else None
    tr = None
    
    details_list = []
    if test:
        tr = db_session.query(TestResult).filter(TestResult.testId == test.id, TestResult.studentId == app.studentId).first()
        
        # Parse answers nếu có
        if tr is not None and getattr(tr, "answers", None):
            try:
                raw_answers = getattr(tr, "answers")
                if not isinstance(raw_answers, (str, bytes, bytearray)):
                    raw_answers = str(raw_answers)
                student_answers = json.loads(raw_answers)
                questions = db_session.query(Question).filter(Question.testId == test.id).all()
                for q in questions:
                    ans_key = f"answer_{q.id}"
                    details_list.append({
                        "question": q.content,
                        "answer": student_answers.get(ans_key, "(Không trả lời)")
                    })
            except (TypeError, ValueError, json.JSONDecodeError):
                pass

    return jsonify({
        "status": serialize_status(app.status),
        "hasTest": bool(test),
        "submitted": bool(tr),
        "score": tr.score if tr else 0,
        "details": details_list
    })

@company_bp.route("/companies/applications/<int:app_id>/cv", methods=["GET"])
def company_view_candidate_cv(app_id):
    app = db_session.query(Application).filter(Application.id == app_id).first()
    if not app: return jsonify({"detail": "Application not found"}), 404

    student = app.student
    profile = student.profile
    
    skills_list = []
    if student.skills:
        skills_list = [{"name": s.skill.name, "level": s.level} for s in student.skills if s.skill]

    return jsonify({
        "applicationId": app.id,
        "jobTitle": app.job.title,
        "appliedAt": app.appliedAt,
        "status": serialize_status(app.status),
        "studentId": student.id,
        "studentName": student.fullName,
        "major": student.major,
        "dob": student.dob.isoformat() if student.dob else None,
        "cccd": getattr(student, "cccd", None),
        "cvUrl": profile.cvUrl if profile else None,
        "portfolioUrl": getattr(profile, "portfolioUrl", None),
        "about": profile.about if profile else "",
        "educationLevel": profile.educationLevel if profile else "",
        "degrees": profile.degrees if profile else "",
        "skills": skills_list
    })

@company_bp.route("/applications/<int:app_id>/evaluate", methods=["POST"])
def evaluate_application(app_id):
    data = request.json
    try:
        app = db_session.query(Application).filter(Application.id == app_id).first()
        if not app: return jsonify({"detail": "Application not found"}), 404
        
        current_status = str(serialize_status(app.status))
        next_status = data.get("nextStatus")

        msg = ""

        # LOGIC 1: PENDING/TESTING -> INTERVIEW
        if next_status == 'interview' and current_status in ['pending', 'testing']:
            # Lưu Evaluation
            db_session.add(Evaluation(
                applicationId=app.id,
                skillScore=data.get("skillScore"),
                peerReview=data.get("peerReview"),
                improvement=data.get("improvement")
            ))
            
            # Cập nhật trạng thái
            app.status = ApplicationStatus.INTERVIEW.value
            
            # Tạo lịch phỏng vấn
            interview_time = None
            if data.get("interviewTime"):
                try:
                    interview_time = datetime.strptime(data.get("interviewTime"), "%Y-%m-%dT%H:%M")
                except ValueError:
                    pass # Keep None if format error
            
            db_session.add(Interview(
                applicationId=app.id,
                interviewDate=interview_time,
                location=data.get("interviewLocation"),
                note=data.get("interviewNote"),
                status="Scheduled"
            ))
            
            time_display = data.get("interviewTime", "").replace("T", " ")
            msg = f"🎉 Hồ sơ '{app.job.title}' được DUYỆT phỏng vấn. ⏰ {time_display}."

        # LOGIC 2: INTERVIEW -> OFFERED/REJECTED
        elif current_status == 'interview':
            # Tìm buổi phỏng vấn gần nhất để cập nhật feedback
            interview = db_session.query(Interview).filter(Interview.applicationId == app.id).order_by(Interview.id.desc()).first()
            if interview:
                db_session.add(InterviewFeedback(
                    interviewId=interview.id,
                    feedback=data.get("interviewFeedback"),
                    rating=safe_int(data.get("interviewRating"))
                ))
                interview.status = "Completed"

            if next_status == 'offered':
                app.status = ApplicationStatus.OFFERED.value
                msg = f"💌 CHÚC MỪNG! Bạn nhận được OFFER cho vị trí '{app.job.title}'."
            elif next_status == 'rejected':
                app.status = ApplicationStatus.REJECTED.value
                msg = f"⚠️ Kết quả phỏng vấn vị trí '{app.job.title}': Chưa phù hợp."

        # LOGIC 3: REJECT TRỰC TIẾP
        elif next_status == 'rejected':
            app.status = ApplicationStatus.REJECTED.value
            msg = f"⚠️ Hồ sơ '{app.job.title}' bị từ chối."

        # Gửi thông báo nếu có
        if msg:
            db_session.add(Notification(userId=app.student.userId, content=msg))

        db_session.commit()
        return jsonify({"message": "Đánh giá thành công", "newStatus": serialize_status(app.status)})

    except Exception as e:
        db_session.rollback()
        print(f"Evaluate Error: {e}")
        return jsonify({"detail": f"Lỗi xử lý: {str(e)}"}), 500