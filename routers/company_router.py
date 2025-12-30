from flask import Blueprint, request, jsonify
from database import db_session
# Import models chính xác từ các file tương ứng
from models.job_models import Job, SkillTest, Question
from models.user_models import Company, Student
from models.app_models import Application, ApplicationStatus, Evaluation, TestResult, Interview, Notification

company_bp = Blueprint("company_router", __name__)

# =========================
# GET ALL JOBS BY COMPANY (MỚI - ĐỂ FIX LỖI HÌNH 3)
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
# CREATE JOB & TEST (GỘP CHUNG - ĐÃ FIX)
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
            maxApplicants=data.get("maxApplicants")
        )
        db_session.add(new_job)
        db_session.flush() 
        # 2. KIỂM TRA & TẠO BÀI TEST
        test_data = data.get("test")       
        if test_data:
            new_test = SkillTest(
                jobId=new_job.id,
                testName=test_data.get("testName", f"Test for {new_job.title}"),
                duration=test_data.get("duration", 30),
                totalScore=test_data.get("totalScore", 100)
            )
            db_session.add(new_test)
            db_session.flush() 
            # 3. TẠO CÂU HỎI
            questions_data = test_data.get("questions", [])
            for q in questions_data:
                new_question = Question(
                    testId=new_test.id,
                    content=q["content"],
                    # Đảm bảo options lưu dưới dạng chuỗi nếu model yêu cầu
                    options=str(q["options"]), 
                    correctAnswer=q["correctAnswer"]
                )
                db_session.add(new_question)
        # 4. LƯU TẤT CẢ VÀO DB
        db_session.commit()
        return jsonify({
            "message": "Đã tạo công việc và bài test thành công",
            "job": {
                "id": new_job.id,
                "title": new_job.title
            },
            "hasTest": True if test_data else False
        }), 201
    except Exception as e:
        db_session.rollback() 
        print(f"Error creating job: {e}") 
        return jsonify({"detail": f"Lỗi khi tạo job: {str(e)}"}), 500


# =========================
# CREATE SKILL TEST FOR JOB (GIỮ LẠI - DÙNG CHO JOB ĐÃ CÓ)
# =========================
@company_bp.route("/jobs/<int:job_id>/test", methods=["POST"])
def create_skill_test(job_id):
    data = request.json

    # 1. Tạo bài Test
    test = SkillTest(
        jobId=job_id,
        testName=data["testName"],
        duration=data["duration"],
        totalScore=data.get("totalScore", 100) # Mặc định 100 nếu không gửi
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test) # Lấy ID của test vừa tạo

    # 2. Lưu danh sách câu hỏi (Nếu có)
    if "questions" in data and isinstance(data["questions"], list):
        for q in data["questions"]:
            new_question = Question(
                testId=test.id,
                content=q["content"],
                options=q["options"], 
                correctAnswer=q["correctAnswer"]
            )
            db_session.add(new_question)    
        db_session.commit()
    return jsonify({
        "id": test.id,
        "testName": test.testName,
        "message": "Đã tạo bài test và câu hỏi thành công"
    }), 201


# =========================
# VIEW APPLICATIONS (DASHBOARD CÔNG TY)
# =========================
@company_bp.route("/companies/<int:company_id>/applications", methods=["GET"])
def get_all_applications_for_company(company_id):
    # Cách đơn giản và an toàn hơn:
    apps = db_session.query(Application).join(Job).filter(Job.companyId == company_id).all()   
    response = []
    for app in apps:
        student = app.student
        job = app.job        
        # Tìm điểm test (nếu có)
        test_score = "N/A"
        # Logic: Tìm test result khớp với bài test của job này
        if job.skill_tests: 
            # Lưu ý: trong models Job.skill_tests đang là list, lấy phần tử đầu tiên
            current_test = job.skill_tests[0] if isinstance(job.skill_tests, list) and job.skill_tests else job.skill_tests           
            # Tìm kết quả
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
# XEM KẾT QUẢ KIỂM TRA THEO VỊ TRÍ CÔNG VIỆC
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
# EVALUATE APPLICATIONS (CÓ GỬI THÔNG BÁO)
# =========================
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
        app = db_session.query(Application).filter(Application.id == app_id).first()       
        if app:
            next_status = data.get("nextStatus") # 'interview' hoặc 'rejected'
            notif_content = ""
            # Xử lý logic trạng thái
            if next_status == "interview":
                app.status = ApplicationStatus.INTERVIEW
                notif_content = f"🎉 Chúc mừng! Hồ sơ ứng tuyển '{app.job.title}' của bạn đã được DUYỆT phỏng vấn."
            elif next_status == "rejected":
                app.status = ApplicationStatus.REJECTED
                notif_content = f"⚠️ Rất tiếc, hồ sơ ứng tuyển '{app.job.title}' của bạn đã bị từ chối."
            # C. Gửi thông báo cho Student (Dựa vào userId của student)
            if notif_content and app.student:
                new_notif = Notification(
                    userId=app.student.userId, # Quan trọng: Gửi vào ID user của sinh viên
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
# GET JOB DETAIL (LẤY CHI TIẾT ĐỂ SỬA)
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
# UPDATE JOB (CẬP NHẬT JOB & TEST)
# =========================
@company_bp.route("/jobs/<int:job_id>", methods=["PUT"])
def update_job(job_id):
    """API cập nhật thông tin job và bài test đi kèm"""
    data = request.json
    job = db_session.query(Job).filter(Job.id == job_id).first()
    if not job:
        return jsonify({"detail": "Job not found"}), 404
    try:
        # 1. Cập nhật thông tin cơ bản của Job
        if "title" in data: job.title = data["title"]
        if "description" in data: job.description = data["description"]
        if "location" in data: job.location = data["location"]
        if "status" in data: job.status = data["status"]
        if "maxApplicants" in data:job.maxApplicants = data["maxApplicants"]
        # 2. Xử lý cập nhật bài Test (nếu có gửi kèm)
        if "test" in data:
            test_data = data["test"]           
            # Tìm bài test cũ của job này (nếu có)
            skill_test = db_session.query(SkillTest).filter(SkillTest.jobId == job.id).first()
            if not skill_test:
                # Nếu chưa có thì tạo mới
                skill_test = SkillTest(
                    jobId=job.id,
                    testName=test_data.get("testName", f"Test for {job.title}"),
                    duration=test_data.get("duration", 30),
                    totalScore=test_data.get("totalScore", 100)
                )
                db_session.add(skill_test)
                db_session.flush() # Lấy ID
            else:
                # Nếu có rồi thì update thông tin
                skill_test.testName = test_data.get("testName", skill_test.testName)
                skill_test.duration = test_data.get("duration", skill_test.duration)
                skill_test.totalScore = test_data.get("totalScore", skill_test.totalScore)
            # 3. Cập nhật câu hỏi (Xóa cũ thêm mới cho đơn giản)
            questions_data = test_data.get("questions", [])
            if questions_data:
                # Xóa câu hỏi cũ
                db_session.query(Question).filter(Question.testId == skill_test.id).delete()                
                # Thêm câu hỏi mới
                for q in questions_data:
                    new_q = Question(
                        testId=skill_test.id,
                        content=q["content"],
                        options=str(q["options"]), # Lưu options dạng chuỗi
                        correctAnswer=q["correctAnswer"]
                    )
                    db_session.add(new_q)
        db_session.commit()
        return jsonify({"message": "Cập nhật thành công", "id": job.id})
    except Exception as e:
        db_session.rollback()
        print(f"Update error: {e}")
        return jsonify({"detail": f"Lỗi cập nhật: {str(e)}"}), 500
    


# =========================
# GET APPLICATIONS BY JOB ID (THÊM MỚI ĐỂ FIX LỖI HÌNH 2)
# =========================
@company_bp.route("/jobs/<int:job_id>/applications", methods=["GET"])
def get_applications_by_job(job_id):
    """Lấy danh sách ứng viên chỉ thuộc về một Job cụ thể"""
    # 1. Tìm tất cả đơn ứng tuyển có jobId khớp
    apps = db_session.query(Application).filter(Application.jobId == job_id).all() 
    response = []
    for app in apps:
        student = app.student       
        # Lấy thêm thông tin CV url an toàn
        cv_url = "#"
        if hasattr(student, 'profile') and student.profile:
            cv_url = student.profile.cvUrl
        response.append({
            "applicationId": app.id,
            "studentName": student.fullName,
            "status": app.status.value if hasattr(app.status, 'value') else app.status,
            "cvUrl": cv_url,
            # Nếu muốn hiển thị thêm điểm test thì thêm logic query TestResult ở đây giống API dashboard
        })
    return jsonify(response)