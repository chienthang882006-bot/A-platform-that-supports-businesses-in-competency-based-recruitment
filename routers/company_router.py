from datetime import datetime
from flask import Blueprint, request, jsonify
from database import db_session
# Import models chính xác từ các file tương ứng
from models.job_models import Job, SkillTest, Question
from models.user_models import Company, Student, CompanyProfile
from models.app_models import Application, ApplicationStatus, Evaluation, TestResult, Interview, Notification
import json
company_bp = Blueprint("company_router", __name__)

def safe_int(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(value)
    except (ValueError, TypeError):
        return default
# =========================
# GET ALL JOBS BY COMPANY
# =========================
@company_bp.route("/companies/<int:company_id>/jobs", methods=["GET"])
def get_jobs_by_company(company_id):
    """Lấy toàn bộ danh sách công việc của một công ty cụ thể"""
    jobs = db_session.query(Job).filter(Job.companyId == company_id).all()   
    response = []
    for job in jobs:
        applied_count = db_session.query(Application).filter(
            Application.jobId == job.id
        ).count()
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
# GET COMPANY PROFILE BY USER
# =========================
@company_bp.route("/companies/user/<int:user_id>/profile", methods=["GET"])
def get_company_profile(user_id):
    # BƯỚC 1: Lấy thông tin cơ bản từ bảng Company
    company = db_session.query(Company).filter(
        Company.userId == user_id
    ).first()

    if not company:
        return jsonify({"detail": "Company not found"}), 404

    # BƯỚC 2: Lấy thông tin chi tiết từ bảng CompanyProfile
    # Dùng company.id để tìm profile tương ứng
    profile = db_session.query(CompanyProfile).filter(
        CompanyProfile.companyId == company.id
    ).first()

    # BƯỚC 3: Gộp dữ liệu trả về
    return jsonify({
        # --- Dữ liệu từ bảng Company ---
        "id": company.id,
        "companyName": company.companyName, 
        
        # --- Dữ liệu từ bảng CompanyProfile ---
        # Kiểm tra "if profile" vì có thể công ty mới tạo chưa có profile
        "description": profile.description if profile else "",
        "website": profile.website if profile else "",
        "address": profile.address if profile else "",
        "industry": profile.industry if profile else "",
        "size": profile.size if profile else "",
        "logoUrl": profile.logoUrl if profile else ""
    })

# =========================
# UPDATE COMPANY PROFILE
# =========================
@company_bp.route("/companies/<int:company_id>/profile", methods=["PUT"])
def update_company_profile(company_id):
    data = request.json

    # BƯỚC 1: Tìm công ty trong bảng Company
    company = db_session.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        return jsonify({"detail": "Company not found"}), 404

    try:
        # BƯỚC 2: Cập nhật tên công ty (Bảng Company)
        if "companyName" in data:
            company.companyName = data["companyName"]

        # BƯỚC 3: Tìm hoặc Tạo mới Profile (Bảng CompanyProfile)
        profile = db_session.query(CompanyProfile).filter(
            CompanyProfile.companyId == company.id
        ).first()
        
        # Nếu chưa có profile thì tạo mới (INSERT)
        if not profile:
            profile = CompanyProfile(companyId=company.id)
            db_session.add(profile)
            db_session.flush() # Flush để object profile sẵn sàng nhận dữ liệu

        # BƯỚC 4: Cập nhật thông tin chi tiết vào Profile
        if "description" in data: profile.description = data["description"]
        if "website" in data: profile.website = data["website"]
        if "address" in data: profile.address = data["address"]
        if "industry" in data: profile.industry = data["industry"]
        if "size" in data: profile.size = data["size"]
        if "logoUrl" in data: profile.logoUrl = data["logoUrl"]

        # BƯỚC 5: Lưu tất cả thay đổi
        db_session.commit()
        return jsonify({"message": "Cập nhật hồ sơ công ty thành công"})

    except Exception as e:
        db_session.rollback()
        print("Update company profile error:", e)
        return jsonify({
            "detail": f"Lỗi cập nhật hồ sơ công ty: {str(e)}"
        }), 500
# =========================
# CREATE JOB & TEST
# =========================
@company_bp.route("/jobs/", methods=["POST"])
def create_job():
    data = request.json
    try:
        # 1. TẠO JOB
        new_job = Job(
            companyId=data["companyId"],
            title=data["title"],
            description=data["description"],
            location=data.get("location"),
            status=data.get("status", "open"),
            maxApplicants=safe_int(data.get("maxApplicants"), 0) # Fix lỗi int
        )
        db_session.add(new_job)
        db_session.flush() 

        # 2. KIỂM TRA & TẠO BÀI TEST
        test_data = data.get("test")       
        if test_data:
            # Fix lỗi duration/totalScore bị None
            t_duration = safe_int(test_data.get("duration"), 30)
            t_score = safe_int(test_data.get("totalScore"), 100)
            
            new_test = SkillTest(
                jobId=new_job.id,
                testName=test_data.get("testName", f"Test for {new_job.title}"),
                duration=t_duration,
                totalScore=t_score
            )
            db_session.add(new_test)
            db_session.flush() 

            # 3. TẠO CÂU HỎI
            questions_data = test_data.get("questions", [])
            for q in questions_data:
                new_question = Question(
                    testId=new_test.id,
                    content=q["content"],
                    options=str(q["options"]), 
                    correctAnswer=q["correctAnswer"]
                )
                db_session.add(new_question)

        db_session.commit()
        return jsonify({
            "message": "Đã tạo công việc thành công",
            "job": {"id": new_job.id, "title": new_job.title}
        }), 201
    except Exception as e:
        db_session.rollback() 
        print(f"Error creating job: {e}") 
        return jsonify({"detail": f"Lỗi khi tạo job: {str(e)}"}), 500


# =========================
# GET ALL OPEN JOBS (Dành cho trang Student Home)
# =========================
@company_bp.route("/jobs/", methods=["GET"])
def get_all_open_jobs():
    # 1. Lấy tất cả job có trạng thái 'open'
    jobs = db_session.query(Job).filter(Job.status == "open").order_by(Job.createdAt.desc()).all()
    
    response = []
    for job in jobs:
        # 2. Kiểm tra xem job này có bài test không
        has_test = False
        test_id = None
        
        # job.skill_tests là một list do quan hệ 1-n
        if job.skill_tests and len(job.skill_tests) > 0:
            has_test = True
            test_id = job.skill_tests[0].id
            
        response.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "location": job.location,
            "status": job.status,
            "companyId": job.companyId,
            "maxApplicants": job.maxApplicants,
            # Hai trường quan trọng để app.py hiển thị nút "Làm bài test" hay "Ứng tuyển"
            "hasTest": has_test,
            "testId": test_id
        })
        
    return jsonify(response)
# =========================
# CREATE SKILL TEST FOR JOB
# =========================
@company_bp.route("/jobs/<int:job_id>/test", methods=["POST"])
def create_skill_test(job_id):
    data = request.json
    try:
        # Fix lỗi duration bị None
        t_duration = safe_int(data.get("duration"), 30)
        t_score = safe_int(data.get("totalScore"), 100)
        
        test = SkillTest(
            jobId=job_id,
            testName=data.get("testName", "Skill Test"),
            duration=t_duration,
            totalScore=t_score
        )
        db_session.add(test)
        db_session.commit()
        db_session.refresh(test)

        if "questions" in data and isinstance(data["questions"], list):
            for q in data["questions"]:
                new_question = Question(
                    testId=test.id,
                    content=q["content"],
                    options=str(q.get("options", "")), 
                    correctAnswer=q["correctAnswer"]
                )
                db_session.add(new_question)    
            db_session.commit()
            
        return jsonify({"id": test.id, "message": "Đã tạo bài test thành công"}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"detail": f"Lỗi tạo bài test: {str(e)}"}), 500
# =========================
# API MỚI: LẤY CHI TIẾT BÀI LÀM CỦA ỨNG VIÊN (Kèm câu hỏi & trả lời)
# =========================
@company_bp.route("/applications/<int:app_id>/test-detail", methods=["GET"])
def get_application_test_detail(app_id):
    # 1. Tìm Application
    app = db_session.query(Application).filter(Application.id == app_id).first()
    if not app: return jsonify({"detail": "App not found"}), 404

    job = app.job
    student = app.student
    
    # 2. Kiểm tra Job có bài test không
    test = db_session.query(SkillTest).filter(SkillTest.jobId == job.id).first()
    if not test:
        return jsonify({"hasTest": False})

    # 3. Tìm kết quả bài làm (TestResult)
    tr = db_session.query(TestResult).filter(
        TestResult.testId == test.id,
        TestResult.studentId == student.id
    ).first()

    if not tr:
        return jsonify({"hasTest": True, "submitted": False})

    # 4. Lấy danh sách câu hỏi để map với câu trả lời
    questions = db_session.query(Question).filter(Question.testId == test.id).all()
    
    # 5. Parse câu trả lời từ JSON string sang Dict
    student_answers = {}
    if tr.answers:
        try:
            student_answers = json.loads(tr.answers)
        except:
            student_answers = {}

    # 6. Ghép Câu hỏi + Câu trả lời
    details_list = []
    for q in questions:
        # Key lưu bên student là "answer_{id}"
        ans_key = f"answer_{q.id}"
        user_ans = student_answers.get(ans_key, "(Không trả lời)")
        details_list.append({
            "question": q.content,
            "answer": user_ans
        })

    return jsonify({
        "hasTest": True,
        "submitted": True,
        "score": tr.score,
        "details": details_list
    })
# =========================
# VIEW APPLICATIONS (DASHBOARD CÔNG TY)
# =========================
@company_bp.route("/companies/<int:company_id>/applications", methods=["GET"])
def get_all_applications_for_company(company_id):
    apps = db_session.query(Application).join(Job).filter(Job.companyId == company_id).all()   
    response = []
    for app in apps:
        student = app.student
        job = app.job        
        # Tìm điểm test (nếu có)
        test_score = "N/A"
        if job.skill_tests: 
            current_test = job.skill_tests[0] if isinstance(job.skill_tests, list) and job.skill_tests else job.skill_tests           
            tr = db_session.query(TestResult).filter(
                TestResult.studentId == student.id,
                TestResult.testId == current_test.id
            ).first()
            if tr:
                test_score = tr.score
        response.append({
            "applicationId": app.id,
            "studentName": student.fullName,
            "jobTitle": job.title,
            "appliedAt": app.appliedAt,
            "status": app.status.value if hasattr(app.status, 'value') else app.status,
            "testScore": test_score,
            "cvUrl": student.profile.cvUrl if (hasattr(student, 'profile') and student.profile) else None
        })
    return jsonify(response)


# =========================
# XEM KẾT QUẢ KIỂM TRA
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
            "score": r.score,
            "submittedAt": r.submittedAt
        })
    return jsonify(response)


# =========================
# EVALUATE APPLICATIONS (CẬP NHẬT: GỬI LỊCH PHỎNG VẤN)
# =========================
# Trong routers/company_router.py

@company_bp.route("/applications/<int:app_id>/evaluate", methods=["POST"])
def evaluate_application(app_id):
    data = request.json
    try:
        # A. Lưu đánh giá chuyên môn
        evaluation = Evaluation(
            applicationId=app_id,
            skillScore=data.get("skillScore"),
            peerReview=data.get("peerReview"),
            improvement=data.get("improvement")
        )
        db_session.add(evaluation)
        
        # B. Cập nhật trạng thái Application & Tạo thông báo
        # ⚠️ ĐỔI TÊN BIẾN 'app' -> 'application' ĐỂ TRÁNH LỖI TRÙNG TÊN
        application = db_session.query(Application).filter(Application.id == app_id).first()       
        
        if application:
            next_status = data.get("nextStatus") # 'interview' hoặc 'rejected'
            notif_content = ""
            
            # 1. TRƯỜNG HỢP DUYỆT PHỎNG VẤN
            if next_status == "interview":
                application.status = ApplicationStatus.INTERVIEW
                
                # Lấy thông tin từ request
                interview_time_str = data.get("interviewTime")      
                interview_location = data.get("interviewLocation")
                interview_note = data.get("interviewNote")

                try:
                    # Xử lý thời gian: Chuyển chuỗi sang datetime object
                    final_time = None
                    if interview_time_str:
                        # Input datetime-local trả về dạng "YYYY-MM-DDTHH:MM"
                        final_time = datetime.strptime(interview_time_str, "%Y-%m-%dT%H:%M")

                    # Lưu vào bảng Interview (Dùng tên cột chuẩn trong models)
                    new_interview = Interview(
                        applicationId=application.id,  # Dùng biến application
                        interviewDate=final_time,      # ⚠️ Sửa scheduleTime -> interviewDate
                        location=interview_location,
                        note=interview_note,
                        status="Scheduled"
                    )
                    db_session.add(new_interview)
                    
                except Exception as ex_inv:
                    print(f"❌ Lỗi lưu interview record: {ex_inv}")

                # Tạo nội dung thông báo chi tiết
                # Format lại giờ hiển thị cho đẹp (bỏ chữ T)
                time_display = interview_time_str.replace("T", " ") if interview_time_str else "Chưa xác định"
                
                notif_content = f"🎉 Chúc mừng! Hồ sơ '{application.job.title}' đã được DUYỆT phỏng vấn."
                if interview_time_str:
                    notif_content += f" ⏰ Thời gian: {time_display}."
                if interview_location:
                    notif_content += f" 📍 Địa điểm: {interview_location}."
                if interview_note:
                    notif_content += f" 📝 Ghi chú: {interview_note}."

            # 2. TRƯỜNG HỢP TỪ CHỐI
            elif next_status == "rejected":
                application.status = ApplicationStatus.REJECTED
                notif_content = f"⚠️ Rất tiếc, hồ sơ ứng tuyển '{application.job.title}' của bạn đã bị từ chối."

            # C. Gửi thông báo cho Student
            if notif_content and application.student:
                new_notif = Notification(
                    userId=application.student.userId,
                    content=notif_content,
                    isRead=False
                )
                db_session.add(new_notif)

        db_session.commit()
        return jsonify({"message": "Đã đánh giá và gửi thông báo thành công"}), 201
        
    except Exception as e:
        db_session.rollback()
        print(f"Lỗi đánh giá: {e}")
        return jsonify({"detail": f"Lỗi server: {str(e)}"}), 500

# =========================
# GET JOB DETAIL
# =========================
@company_bp.route("/jobs/<int:job_id>", methods=["GET"])
def get_job_detail(job_id):
    """API lấy thông tin chi tiết một job theo ID"""
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



# =========================
# UPDATE JOB 
# =========================
# =========================
# UPDATE JOB (BẢN SỬA LỖI HOÀN CHỈNH - HẾT BÁO ĐỎ)
# =========================
@company_bp.route("/jobs/<int:job_id>", methods=["PUT"])
def update_job(job_id):
    # 1. Lấy dữ liệu an toàn
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"detail": "Không có dữ liệu gửi lên"}), 400

    job = db_session.query(Job).filter(Job.id == job_id).first()
    if not job:
        return jsonify({"detail": "Job not found"}), 404
        
    try:
        # 2. Cập nhật thông tin cơ bản
        # Ép kiểu str() để VS Code Pylance không báo lỗi
        if "title" in data:
            val = data.get("title")
            if val is not None: job.title = str(val)
            
        if "description" in data:
            val = data.get("description")
            if val is not None: job.description = str(val)
            
        if "location" in data:
            val = data.get("location")
            if val is not None: job.location = str(val)
            
        if "status" in data:
            val = data.get("status")
            if val is not None: job.status = str(val)
        
        # Dùng safe_int để sửa lỗi "int() argument must be..."
        if "maxApplicants" in data:
            job.maxApplicants = safe_int(data.get("maxApplicants"), 0)

        # 3. Cập nhật bài Test
        test_source = None
        if "test" in data and isinstance(data["test"], dict):
            test_source = data["test"]
        elif "testName" in data: 
            test_source = data

        if test_source:
            # Chuyển đổi an toàn về dict nếu test_source đang là string
            test_dict = test_source if isinstance(test_source, dict) else {"testName": str(test_source)}

            skill_test = db_session.query(SkillTest).filter(SkillTest.jobId == job.id).first()
            
            # Lấy giá trị an toàn (QUAN TRỌNG: Fix lỗi duration khi edit thời gian)
            t_name = str(test_dict.get("testName") or "")
            t_duration = safe_int(test_dict.get("duration"), 30)
            t_score = safe_int(test_dict.get("totalScore"), 100)

            if t_name: 
                if not skill_test:
                    skill_test = SkillTest(
                        jobId=job.id,
                        testName=t_name,
                        duration=t_duration,
                        totalScore=t_score
                    )
                    db_session.add(skill_test)
                    db_session.flush()
                else:
                    skill_test.testName = t_name
                    skill_test.duration = t_duration
                    skill_test.totalScore = t_score
                
                # 4. Cập nhật câu hỏi
                questions_data = test_dict.get("questions")
                if questions_data and isinstance(questions_data, list):
                    db_session.query(Question).filter(Question.testId == skill_test.id).delete()                
                    for q in questions_data:
                        new_q = Question(
                            testId=skill_test.id,
                            content=str(q.get("content") or ""),
                            options=str(q.get("options") or ""), 
                            correctAnswer=str(q.get("correctAnswer") or "")
                        )
                        db_session.add(new_q)

        db_session.commit()
        return jsonify({"message": "Cập nhật thành công", "id": job.id})

    except Exception as e:
        db_session.rollback()
        print(f"Update error: {e}") 
        return jsonify({"detail": f"Lỗi cập nhật: {str(e)}"}), 500
# =========================
# GET APPLICATIONS BY JOB ID
# =========================
@company_bp.route("/jobs/<int:job_id>/applications", methods=["GET"])
def get_applications_by_job(job_id):
    apps = db_session.query(Application).filter(Application.jobId == job_id).all() 
    response = []
    for app in apps:
        student = app.student       
        cv_url = "#"
        if hasattr(student, 'profile') and student.profile:
            cv_url = student.profile.cvUrl
        response.append({
            "applicationId": app.id,
            "studentName": student.fullName,
            "status": app.status.value if hasattr(app.status, 'value') else app.status,
            "cvUrl": cv_url,
        })
    return jsonify(response)

# ========================= 
# XEM CHI TIẾT HỒ SƠ ỨNG VIÊN (ĐÃ FIX LỖI KEY ERROR)
# =========================
@company_bp.route("/companies/applications/<int:app_id>/cv", methods=["GET"])
def company_view_candidate_cv(app_id):
    # 1. Lấy Application
    app = db_session.query(Application).filter(Application.id == app_id).first()
    if not app:
        return jsonify({"detail": "Application not found"}), 404

    student = app.student
    if not student:
        return jsonify({"detail": "Không tìm thấy thông tin ứng viên"}), 404

    profile = student.profile
    
    # 2. Lấy danh sách kỹ năng
    skills_list = []
    if student.skills:
        for s in student.skills:
            skill_name = s.skill.name if s.skill else "Unknown Skill"
            skills_list.append({
                "name": skill_name,
                "level": s.level
            })

    # 3. Trả về dữ liệu (Đã sửa lại key 'studentName' cho khớp với giao diện)
    response_data = {
        "applicationId": app.id,
        "jobTitle": app.job.title,
        "appliedAt": app.appliedAt,
        "status": app.status.value if hasattr(app.status, 'value') else app.status,

        # QUAN TRỌNG: Giữ nguyên key là 'studentName' để giao diện không bị lỗi
        "studentId": student.id,
        "studentName": student.fullName,  # <--- Đã sửa từ fullName thành studentName
        "major": student.major,
        "dob": student.dob.isoformat() if student.dob else None,
        "cccd": getattr(student, "cccd", None),

        "cvUrl": profile.cvUrl if profile else None,
        "portfolioUrl": getattr(profile, "portfolioUrl", None),
        "about": profile.about if profile else "",
        "educationLevel": profile.educationLevel if profile else "",
        "degrees": profile.degrees if profile else "",

        "skills": skills_list
    }

    return jsonify(response_data)