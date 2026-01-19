from flask import Blueprint, request, session, redirect, url_for
import requests
import secrets
from utils import wrap_layout, API_URL

student_view_bp = Blueprint('student_view', __name__)

def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(16)
    return session["_csrf_token"]

def validate_csrf(token):
    return token and session.get("_csrf_token") == token

@student_view_bp.route("/student/home")
def student_home():
    if "user" not in session or session["user"]["role"] != "student":
        return redirect("/login")
    csrf_token = generate_csrf_token()

    message = session.pop("apply_message", "")
    jobs = []
    applied_job_ids = []
    done_test_ids = []

    try:
        user_id = session['user']['id']
        stu_res = requests.get(f"{API_URL}/students/user/{user_id}", timeout=5)
        if stu_res.status_code != 200:
            return wrap_layout("<p>⚠️ Không tìm thấy hồ sơ sinh viên</p>")
        stu = stu_res.json()
        student_id = stu["id"]

        try:
            res = requests.get(f"{API_URL}/jobs/", params={"studentId": student_id}, timeout=5)
            jobs = res.json() if res.status_code == 200 else []
        except Exception:
            res = requests.get(f"{API_URL}/jobs/", timeout=5)
            jobs = res.json() if res.status_code == 200 else []

        applied_res = requests.get(f"{API_URL}/students/{student_id}/applications", timeout=5)
        if applied_res.status_code == 200:
            applied_job_ids = [a["jobId"] for a in applied_res.json()]

        test_done_res = requests.get(f"{API_URL}/students/{student_id}/tests", timeout=5)
        if test_done_res.status_code == 200:
            done_test_ids = [t["testId"] for t in test_done_res.json()]

    except Exception as e:
        print("Error loading student/home data:", e)
        jobs = []

    content = f"<h2>💼 Danh sách việc làm</h2><p>{message}</p>"

    for j in jobs:
        job_id = j.get("id")
        has_test = j.get("hasTest", False)
        test_id = j.get("testId", None)

        if job_id in applied_job_ids:
            continue
        if str(j.get("status", "")).upper() == "CLOSED":
            continue

        if has_test and test_id not in done_test_ids:
            content += f"""
            <div class="job-card">
                <h3>{j.get('title','(No title)')}</h3>
                <p>{j.get('description','')}</p>
                <a href="/student/test/{test_id}">
                    <button style="background:#f59e0b">
                        📝 Làm bài test
                    </button>
                </a>
            </div>
            """
        else:
            content += f"""
            <div class="job-card">
                <h3>{j.get('title','(No title)')}</h3>
                <p>{j.get('description','')}</p>
                <form method="post" action="/apply/{job_id}">
                    <input type="hidden" name="csrf_token" value="{csrf_token}">
                    <button>✅ Ứng tuyển</button>
                </form>
            </div>
            """

    return wrap_layout(content)

@student_view_bp.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    if not validate_csrf(request.form.get("csrf_token")):
        return "CSRF token không hợp lệ", 400
    session.pop("_csrf_token", None)

    if 'user' not in session:
        return redirect('/login')
    user_id = session['user']['id']
    stu = requests.get(f"{API_URL}/students/user/{user_id}").json()
    student_id = stu["id"]
    res = requests.post(
        f"{API_URL}/apply/",
        json={"studentId": student_id, "jobId": job_id}
    )
    if res.status_code == 201:
        data = res.json()
        if data.get("status") == "NEED_TEST":
            session["current_job_id"] = job_id
            return redirect(f"/student/test/{data['testId']}")
        if data.get("status") == "APPLIED":
            session["apply_message"] = "✅ Ứng tuyển thành công"
            return redirect("/student/home")
    session["apply_message"] = "❌ Không thể ứng tuyển"
    return redirect("/student/home")

@student_view_bp.route("/student/profile", methods=["GET", "POST"])
def student_profile():
    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            return "CSRF token không hợp lệ", 400
        session.pop("_csrf_token", None)

    if 'user' not in session:
        return redirect('/login')
    
    user_id = session['user']['id']
    stu_res = requests.get(f"{API_URL}/students/user/{user_id}")
    
    if stu_res.status_code != 200:
        return wrap_layout("<p>Không tìm thấy hồ sơ sinh viên</p>")
    
    student = stu_res.json()
    student_id = student["id"]
    profile = student.get("profile") or {}
    skills = student.get("skills", [])
    skills_text = ", ".join([f"{s['name']}:{s['level']}" for s in skills])
    message = ""
    
    if request.method == "POST":
        skills_raw = request.form.get("skills", "")
        skills_list = []
        for item in skills_raw.split(","):
            if ":" in item:
                name, level = item.split(":")
                skills_list.append({
                    "name": name.strip(),
                    "level": int(level.strip())
                })
                
        payload = {
            "fullName": request.form.get("fullName"),
            "major": request.form.get("major"),
            "about": request.form.get("about"),
            "educationLevel": request.form.get("educationLevel"),
            "degrees": request.form.get("degrees"),
            "cvUrl": request.form.get("cvUrl"),
            "portfolioUrl": request.form.get("portfolioUrl"),
            "skills": skills_list
        }
        
        res = requests.put(
            f"{API_URL}/students/{student_id}",
            json=payload
        )
        if res.status_code == 200:
            message = "<p style='color:green;'>✅ Hồ sơ đã được lưu</p>"
            student = requests.get(f"{API_URL}/students/user/{user_id}").json()
            profile = student.get("profile") or {}
            skills = student.get("skills", [])
            skills_text = ", ".join([f"{s['name']}:{s['level']}" for s in skills])
        else:
            message = "<p style='color:red;'>❌ Lưu hồ sơ thất bại</p>"

    content = f"""
    <h2>👤 Thông tin cá nhân</h2>
    {message}
    <form method="post">
        <input type="hidden" name="csrf_token" value="{generate_csrf_token()}">
        <label>Họ tên</label>
        <input name="fullName" value="{student.get('fullName','')}">
        <label>Ngành học</label>
        <input name="major" value="{student.get('major','')}">
        <label>Giới thiệu bản thân</label>
        <textarea name="about" rows="3">{profile.get('about','')}</textarea>
        <label>Trình độ học vấn (VD: Đại học, Cao đẳng)</label>
        <input name="educationLevel" value="{profile.get('educationLevel','')}">
        <label>Bằng cấp / Chứng chỉ</label>
        <input name="degrees" value="{profile.get('degrees','')}">
        <label>Link CV (PDF/Drive)</label>
        <input name="cvUrl" value="{profile.get('cvUrl','')}">
        <label>Link Portfolio</label>
        <input name="portfolioUrl" value="{profile.get('portfolioUrl','')}">
        <label>Kỹ năng (Định dạng: Tên:Level, VD: Python:5, Java:4)</label>
        <input name="skills" value="{skills_text}">
        <button>💾 Lưu hồ sơ</button>
    </form>
    """
    return wrap_layout(content)

@student_view_bp.route('/student/applications')
def student_applications():
    if 'user' not in session: return redirect('/login')
    
    user_id = session['user']['id']
    try:
        # 1. Lấy thông tin sinh viên
        stu_res = requests.get(f"{API_URL}/students/user/{user_id}")
        if stu_res.status_code != 200: 
            return wrap_layout(f"<h2>⚠️ Lỗi: Không tìm thấy sinh viên (API Code {stu_res.status_code})</h2>")
        
        student_data = stu_res.json()
        student_id = student_data['id']

        # 2. Lấy danh sách ứng tuyển (CODE DEBUG)
        app_url = f"{API_URL}/students/{student_id}/applications"
        app_res = requests.get(app_url)
        
        # === NẾU API LỖI, IN RA MÀN HÌNH ĐỂ BẠN THẤY ===
        if app_res.status_code != 200:
            error_html = f"""
            <div style="background:#fee2e2; border:1px solid #ef4444; padding:20px; border-radius:8px; color:#b91c1c;">
                <h3>❌ Lỗi kết nối API lấy danh sách ứng tuyển</h3>
                <p><b>URL:</b> {app_url}</p>
                <p><b>Status Code:</b> {app_res.status_code}</p>
                <p><b>Response Text:</b> {app_res.text}</p>
                <hr>
                <p><i>Hãy chụp màn hình lỗi này để kiểm tra lại file routers/student_router.py</i></p>
            </div>
            """
            return wrap_layout(error_html)
            
        apps = app_res.json()

    except Exception as e:
        return wrap_layout(f"<h2>❌ Lỗi kết nối hệ thống (Python): {e}</h2>")

    # --- Phần hiển thị HTML (khi có dữ liệu) ---
    html = ""
    for a in apps:
        status = a.get('status', 'Unknown')
        
        status_badge = f"<span style='background:#e0f2fe; color:#0284c7; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:12px;'>{status}</span>"
        card_style = "border-left: 5px solid #2563eb;" 
        footer_msg = ""

        if status == 'offered':
            card_style = "border-left: 5px solid #16a34a; background: #f0fdf4;" 
            status_badge = "<span style='background:#16a34a; color:white; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:12px;'>🎉 OFFERED</span>"
            footer_msg = "<div style='margin-top:10px; color:#15803d; font-weight:bold;'>💌 Chúc mừng! Bạn đã nhận được lời mời làm việc.</div>"
        elif status == 'rejected':
            card_style = "border-left: 5px solid #ef4444; background: #fef2f2;" 
            status_badge = "<span style='background:#ef4444; color:white; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:12px;'>❌ REJECTED</span>"
            footer_msg = "<div style='margin-top:10px; color:#b91c1c;'>⚠️ Hồ sơ chưa phù hợp.</div>"
        elif status == 'interview':
            card_style = "border-left: 5px solid #ec4899;" 
            status_badge = "<span style='background:#ec4899; color:white; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:12px;'>🎤 INTERVIEW</span>"
            footer_msg = "<div style='margin-top:10px; color:#be185d;'>📅 Bạn có lịch phỏng vấn.</div>"

        test_btn = ""
        if a.get('hasTest'): 
            if a.get('testStatus') == 'pending':
                test_btn = f"<div style='margin-top:10px;'><a href='/student/test/{a.get('testId')}'><button style='background:#f97316; width:auto; padding:5px 15px; font-size:12px;'>✍️ Làm bài Test ngay</button></a></div>"
            elif a.get('testStatus') == 'done':
                test_btn = "<div style='margin-top:5px; color:green; font-size:13px;'>✅ Đã làm bài test</div>"

        html += f"""
        <div class="job-card" style="{card_style}">
            <div style="display:flex; justify-content:space-between;">
                <h3 style="margin:0;">{a.get('jobTitle', 'Công việc')}</h3>
                {status_badge}
            </div>
            <p style="margin:5px 0; color:#666;">🏢 {a.get('companyName', 'Công ty')}</p>
            <p style="font-size:12px; color:#999;">Ngày ứng tuyển: {a.get('appliedAt', '')}</p>
            {test_btn}
            {footer_msg}
        </div>
        """
    
    if not html:
        html = "<p><i>API trả về thành công (200 OK) nhưng danh sách rỗng. Có thể quá trình ứng tuyển chưa được lưu vào database.</i></p>"

    return wrap_layout(f"<h2>📌 Việc làm đã ứng tuyển</h2>{html}")

@student_view_bp.route("/student/tests/<int:job_id>")
def student_tests(job_id):
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect('/login')
    session["current_job_id"] = job_id
    user_id = session['user']['id']
    stu = requests.get(f"{API_URL}/students/user/{user_id}").json()
    student_id = stu["id"]
    start_res = requests.post(
        f"{API_URL}/tests/start",
        json={"studentId": student_id, "jobId": job_id}
    )
    if start_res.status_code in [200, 201]:
        test_id = start_res.json()["testId"]
        return redirect(f"/student/test/{test_id}")
    return redirect("/student/home")

@student_view_bp.route("/student/test/<int:test_id>")
def student_do_test(test_id):

    if 'user' not in session:
        return redirect('/login')
    user_id = session['user']['id']
    stu_res = requests.get(f"{API_URL}/students/user/{user_id}")
    if stu_res.status_code != 200:
        return wrap_layout("<p>❌ Không tìm thấy sinh viên</p>")
    student_id = stu_res.json()["id"]
    res = requests.get(f"{API_URL}/tests/{test_id}")
    if res.status_code != 200:
        return wrap_layout("<p>❌ Không tìm thấy bài test</p>")
    test = res.json()
    job_id = test.get("jobId")
    if not session.get("current_job_id") and job_id:
        session["current_job_id"] = job_id

    job_to_start = session.get("current_job_id") or job_id
    if not job_to_start:
        return wrap_layout("<p>❌ Bài test chưa liên kết với job</p>")
    start_res = requests.post(
        f"{API_URL}/tests/start",
        json={"studentId": student_id, "jobId": job_to_start}
    )
    if start_res.status_code not in [200, 201]:
        try:
            msg = start_res.json().get("detail") or start_res.text
        except:
            msg = start_res.text
        return wrap_layout(f"<p>❌ Không thể bắt đầu bài test: {msg}</p>")
    questions_html = ""
    for idx, q in enumerate(test.get("questions", []), start=1):
        questions_html += f"""
        <div class="job-card">
            <b>Câu {idx}:</b> {q['content']}<br>
            <textarea name="answer_{q['id']}" placeholder="Nhập câu trả lời tự luận của bạn..." required rows="5" style="width:100%; margin-top:10px;"></textarea>
        </div>
        """
    content = f"""
    <h2>📝 {test.get('testName')}</h2>
    <p>⏱ Thời gian: {test.get('duration')} phút</p>
    <form method="post" action="/student/test/submit/{test_id}">
        <input type="hidden" name="csrf_token" value="{generate_csrf_token()}">
        <input type="hidden" name="jobId" value="{job_to_start}">
        {questions_html}
        <button type="submit" style="margin-top:20px;">📤 Nộp bài test</button>
    </form>
    """
    return wrap_layout(content)

@student_view_bp.route("/student/test/submit/<int:test_id>", methods=["POST"])
def student_test_submit(test_id):
    if not validate_csrf(request.form.get("csrf_token")):
        return "CSRF token không hợp lệ", 400
    session.pop("_csrf_token", None)

    if 'user' not in session:
        return redirect('/login')
    user_id = session['user']['id']
    stu_res = requests.get(f"{API_URL}/students/user/{user_id}")
    if stu_res.status_code != 200:
        session["apply_message"] = "❌ Lỗi: không tìm thấy sinh viên"
        return redirect("/student/home")
    student_id = stu_res.json()["id"]
    answers = dict(request.form)
    submit_payload = {
        "studentId": student_id,
        "score": 0,        
        "answers": answers
    }
    submit_res = requests.post(f"{API_URL}/tests/{test_id}/submit", json=submit_payload)
    if submit_res.status_code not in (200, 201):
        try:
            msg = submit_res.json().get("detail") or submit_res.text
        except:
            msg = submit_res.text
        session["apply_message"] = f"❌ Lỗi nộp bài: {msg}"
        return redirect("/student/home")
    job_id = session.pop("current_job_id", None) or request.form.get("jobId")
    if job_id:
        try:
            apply_res = requests.post(
                f"{API_URL}/apply/",
                json={"studentId": student_id, "jobId": int(job_id)}
            )
            if apply_res.status_code in (200, 201):
                data = {}
                try:
                    data = apply_res.json()
                except:
                    data = {}
                if data.get("status") in ("ALREADY_APPLIED", "APPLIED"):
                    session["apply_message"] = "✅ Hoàn thành bài test & đã ứng tuyển"
                elif data.get("status") == "NEED_TEST":
                    session["apply_message"] = "✅ Hoàn thành bài test, hồ sơ đang chờ xét duyệt"
                else:
                    session["apply_message"] = "✅ Hoàn thành bài test"
            else:
                try:
                    err = apply_res.json().get("detail") or apply_res.text
                except:
                    err = apply_res.text
                session["apply_message"] = f"✅ Hoàn thành bài test — nhưng apply lỗi: {err}"
        except Exception as e:
            session["apply_message"] = f"✅ Hoàn thành bài test — nhưng apply thất bại: {e}"
    else:
        session["apply_message"] = "✅ Hoàn thành bài test"
    return redirect("/student/home")