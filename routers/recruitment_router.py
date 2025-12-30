from flask import Blueprint, request, jsonify
from database import db_session
from models import Job, Application, Student, Company, ApplicationStatus, TestResult, SkillTest


recruitment_bp = Blueprint('recruitment_router', __name__)


@recruitment_bp.route("/jobs/", methods=["GET"])
def get_all_jobs():
    student_id = request.args.get("studentId", type=int)
    # lấy job chưa CLOSED
    jobs = db_session.query(Job).filter(Job.status != "CLOSED").all()

    result = []
    for j in jobs:
        applied_count = db_session.query(Application).filter(Application.jobId == j.id).count()

        # nếu job đã đủ người: đóng job và bỏ qua (đảm bảo nhất quán)
        if j.maxApplicants and applied_count >= j.maxApplicants:
            j.status = "CLOSED"
            db_session.commit()
            continue

        # nếu client gửi studentId thì lọc các job student đã apply
        if student_id:
            existed = db_session.query(Application).filter(
                Application.jobId == j.id,
                Application.studentId == student_id
            ).first()
            if existed:
                continue

        result.append({
            "id": j.id,
            "title": j.title,
            "description": j.description,
            "location": j.location,
            "status": j.status,
            "hasTest": True if j.skill_tests else False,
            "testId": j.skill_tests[0].id if j.skill_tests else None,
            "appliedCount": applied_count,
            "maxApplicants": j.maxApplicants
        })
    return jsonify(result)


@recruitment_bp.route("/apply/", methods=["POST"])
def apply_job():
    data = request.json
    student_id = data["studentId"]
    job_id = data["jobId"]

    job = db_session.query(Job).filter(Job.id == job_id).first()
    if not job:
        return jsonify({"detail": "Job không tồn tại"}), 404

    # kiểm tra số lượng trước khi tạo application
    if job.maxApplicants:
        applied_count_before = db_session.query(Application).filter(Application.jobId == job.id).count()
        if applied_count_before >= job.maxApplicants:
            # đóng job nếu đã đầy
            job.status = "CLOSED"
            db_session.commit()
            return jsonify({"detail": "Job đã đủ người"}), 400

    # không cho apply trùng
    existing_app = db_session.query(Application).filter(
        Application.studentId == student_id,
        Application.jobId == job_id
    ).first()
    if existing_app:
        return jsonify({
            "status": "ALREADY_APPLIED",
            "applicationId": existing_app.id
        }), 200

    has_test = bool(job.skill_tests)
    new_app = Application(
        jobId=job_id,
        studentId=student_id,
        status=ApplicationStatus.TESTING if has_test else ApplicationStatus.PENDING
    )
    db_session.add(new_app)
    db_session.commit()

    # sau khi tạo app, kiểm tra lại: nếu đã đạt max -> đóng job
    if job.maxApplicants:
        applied_count_after = db_session.query(Application).filter(Application.jobId == job.id).count()
        if applied_count_after >= job.maxApplicants:
            job.status = "CLOSED"
            db_session.commit()

    if has_test:
        test = job.skill_tests[0]
        return jsonify({
            "status": "NEED_TEST",
            "testId": test.id,
            "applicationId": new_app.id
        }), 201

    return jsonify({
        "status": "APPLIED",
        "applicationId": new_app.id
    }), 201




@recruitment_bp.route("/students/<int:student_id>/applications", methods=["GET"])
def get_student_applications(student_id):
    apps = db_session.query(Application).filter(
        Application.studentId == student_id
    ).all()
    return jsonify([{
        "applicationId": a.id,
        "jobId": a.job.id,
        "jobTitle": a.job.title,
        "status": a.status.value,
        "appliedAt": a.appliedAt.isoformat()
    } for a in apps])


@recruitment_bp.route("/tests/start", methods=["POST"])
def start_test():
    data = request.json
    student_id = data["studentId"]
    job_id = data["jobId"]
    # 1. Lấy bài test của job
    job = db_session.query(Job).filter(Job.id == job_id).first()
    if not job or not job.skill_tests:
        return jsonify({"detail": "Job không có bài test"}), 404
    test = job.skill_tests[0]
    # 2. Kiểm tra đã làm test chưa
    existed = db_session.query(TestResult).filter(
        TestResult.studentId == student_id,
        TestResult.testId == test.id
    ).first()
    if existed:
        return jsonify({
            "message": "Đã làm test",
            "testId": test.id
        }), 200
    # 3. Tạo TestResult (chưa có điểm)
    tr = TestResult(
        studentId=student_id,
        testId=test.id,
        score=0
    )
    db_session.add(tr)
    db_session.commit()
    return jsonify({
        "message": "Bắt đầu làm test",
        "testId": test.id
    }), 201


@recruitment_bp.route("/tests/<int:test_id>/submit", methods=["POST"])
def submit_test(test_id):
    data = request.json or {}
    student_id = data.get("studentId")
    score = data.get("score", 0)
    if not student_id:
        return jsonify({"detail": "studentId required"}), 400
    # 1) kiểm tra TestResult đã tồn tại (student đã start test)
    tr = db_session.query(TestResult).filter(
        TestResult.studentId == student_id,
        TestResult.testId == test_id
    ).first()
    if not tr:
        return jsonify({"detail": "Chưa làm test"}), 404
    # 2) cập nhật điểm cho TestResult
    tr.score = score
    # 3) tìm jobId từ SkillTest (để biết ứng dụng nào cần update)
    job_id = None
    try:
        test = db_session.query(SkillTest).filter(SkillTest.id == test_id).first()
        if test:
            job_id = getattr(test, "jobId", None)
    except Exception:
        job_id = None
    application_updated = False
    app_rec = None
    if job_id:
        # 4) tìm Application của student cho job này — lấy ứng dụng mới nhất (nếu có nhiều)
        app_rec = db_session.query(Application).filter(
            Application.jobId == job_id,
            Application.studentId == student_id
        ).order_by(Application.appliedAt.desc()).first()
        if app_rec:
            # Cố gắng cập nhật enum; nếu model lưu string thì fallback
            try:
                app_rec.status = ApplicationStatus.PENDING
            except Exception:
                app_rec.status = "PENDING"
            application_updated = True
    db_session.commit()
    return jsonify({
        "message": "Nộp bài test thành công",
        "testId": test_id,
        "testResultId": getattr(tr, "id", None),
        "applicationUpdated": application_updated,
        "applicationId": getattr(app_rec, "id", None) if app_rec else None
    }), 200

