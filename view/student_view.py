from flask import Blueprint, request, redirect, make_response
import requests
import secrets
from utils import wrap_layout, API_URL, get_current_user_from_jwt, auth_headers
from markupsafe import escape

student_view_bp = Blueprint('student_view', __name__)

def is_profile_complete(student_data):
    """
    Kiểm tra xem sinh viên đã điền đủ thông tin quan trọng chưa.
    Các trường bắt buộc: fullName, cccd, major, và link CV (cvUrl) trong profile.
    """
    if not student_data.get("fullName"): return False
    if not student_data.get("cccd"): return False
    if not student_data.get("major"): return False
    
    profile = student_data.get("profile")
    if not profile: return False
    if not profile.get("cvUrl"): return False
    
    return True
def require_student_view():
    user = get_current_user_from_jwt()
    if not user:
        return None
    if user.get("role") != "student":
        return None
    return user

def generate_csrf_token():
    return secrets.token_hex(16)

def validate_csrf(form_token):
    cookie_token = request.cookies.get("csrf_token")
    return cookie_token and form_token and cookie_token == form_token


@student_view_bp.route("/student/home")
def student_home():
    user = require_student_view()
    if not user:
        return redirect("/login")

    csrf_token = generate_csrf_token()
    message = request.args.get("msg", "")
    jobs = []
    applied_job_ids = []
    done_test_ids = []

    try:
        user_id = user["id"]
        stu_res = requests.get(
            f"{API_URL}/students/user/{user_id}",
            headers=auth_headers(),
            timeout=5
        )
        if stu_res.status_code != 200:
            return wrap_layout("<p>⚠️ Không tìm thấy hồ sơ sinh viên</p>")
        stu = stu_res.json()
        student_id = stu["id"]

        try:
            res = requests.get(f"{API_URL}/jobs/", headers=auth_headers(), timeout=5)
            jobs = res.json() if res.status_code == 200 else []
        except Exception:
            res = requests.get(f"{API_URL}/jobs/", timeout=5)
            jobs = res.json() if res.status_code == 200 else []

        applied_res = requests.get(f"{API_URL}/students/{student_id}/applications", headers=auth_headers(), timeout=5)
        if applied_res.status_code == 200:
            applied_job_ids = [a["jobId"] for a in applied_res.json()]

        test_done_res = requests.get(f"{API_URL}/students/{student_id}/tests", headers=auth_headers(), timeout=5)
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
                <h3>{escape(j.get('title','(No title)'))}</h3>
                <p>{escape(j.get('description',''))}</p>
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
    resp = make_response(wrap_layout(content))
    resp.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=True,
        samesite="Lax",
        secure=request.is_secure
    )
    return resp


@student_view_bp.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    if not validate_csrf(request.form.get("csrf_token")):
        return "CSRF token không hợp lệ", 400

    user = require_student_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]
    
    # 1. Lấy thông tin sinh viên từ API
    stu_res = requests.get(f"{API_URL}/students/user/{user_id}", headers=auth_headers())
    
    if stu_res.status_code != 200:
        return redirect("/student/home?msg=❌+Lỗi+kết+nối+dữ+liệu+sinh+viên")

    stu = stu_res.json()

    # ==================================================================
    # 2. KIỂM TRA HỒ SƠ ĐẦY ĐỦ (LOGIC MỚI)
    # ==================================================================
    # Các trường bắt buộc phải có giá trị
    required_fields = {
        "fullName": "Họ tên",
        "cccd": "CCCD",
        "major": "Ngành học"
    }
    
    missing = []
    
    # Kiểm tra các trường cơ bản (Level 1)
    for field, label in required_fields.items():
        if not stu.get(field):
            missing.append(label)

    # Kiểm tra Profile và CV (Level 2 - nằm trong object 'profile')
    profile = stu.get("profile")
    if not profile or not profile.get("cvUrl"):
        missing.append("Link CV")

    # Nếu thiếu thông tin -> Chặn và đẩy về trang Profile
    if missing:
        missing_str = ", ".join(missing)
        msg = f"⚠️ Bạn cần cập nhật: {missing_str} trước khi ứng tuyển!"
        return redirect(f"/student/profile?msg={msg}")
    # ==================================================================

    # 3. Nếu hồ sơ OK -> Tiếp tục quy trình ứng tuyển cũ
    student_id = stu["id"]
    res = requests.post(
        f"{API_URL}/apply/",
        json={"studentId": student_id, "jobId": job_id},
        headers=auth_headers()
    )
    if res.status_code == 201:
        data = res.json()
        if data.get("status") == "NEED_TEST":
            return redirect(f"/student/test/{data['testId']}")

        if data.get("status") == "APPLIED":
            return redirect("/student/home?msg=✅+Ứng+tuyển+thành+công")

        return redirect("/student/home?msg=❌+Không+thể+ứng+tuyển")

    return redirect("/student/home")


# Trong file student_view.py

@student_view_bp.route("/student/profile", methods=["GET", "POST"])
def student_profile():
    
    csrf_token = generate_csrf_token()

    # 1. Hiển thị thông báo từ URL (nếu có)
    msg_from_url = request.args.get("msg", "")
    message = ""
    if msg_from_url:
        message = f"<p style='color:#d97706; font-weight:bold; border:1px solid #d97706; padding:10px; background:#fffbeb;'>{msg_from_url}</p>"

    user = require_student_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]
    
    # 2. Lấy thông tin sinh viên hiện tại
    stu_res = requests.get(
        f"{API_URL}/students/user/{user_id}",
        headers=auth_headers(),
        timeout=5
    )
    
    if stu_res.status_code != 200:
        return wrap_layout("<p>Không tìm thấy hồ sơ sinh viên</p>")
    
    student = stu_res.json()
    student_id = student["id"]
    profile = student.get("profile") or {}
    
    # 3. XỬ LÝ LƯU (POST)
    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            return "CSRF token không hợp lệ", 400

        skills_raw = request.form.get("skills", "")
        skills_list = []
        for item in skills_raw.split(","):
            if ":" in item:
                name, level = item.split(":")
                skills_list.append({
                    "name": name.strip(),
                    "level": int(level.strip())
                })
        
        # Payload gửi lên API
        payload = {
            "fullName": request.form.get("fullName"),
            "major": request.form.get("major"),
            "cccd": request.form.get("cccd"),  # <--- Nhận CCCD
            "dob": request.form.get("dob"),    # <--- Nhận Ngày sinh
            "about": request.form.get("about"),
            "educationLevel": request.form.get("educationLevel"),
            "degrees": request.form.get("degrees"),
            "cvUrl": request.form.get("cvUrl"),
            "portfolioUrl": request.form.get("portfolioUrl"),
            "skills": skills_list
        }
        
        res = requests.put(
            f"{API_URL}/students/{student_id}",
            json=payload,
            headers=auth_headers()
        )
        if res.status_code == 200:
            message = "<p style='color:green; font-weight:bold;'>✅ Hồ sơ đã được lưu thành công</p>"
            # Load lại data mới nhất để hiển thị
            student = requests.get(f"{API_URL}/students/user/{user_id}").json()
            profile = student.get("profile") or {}
        else:
            message = "<p style='color:red;'>❌ Lưu hồ sơ thất bại</p>"

    # 4. CHUẨN BỊ DỮ LIỆU HIỂN THỊ
    skills = student.get("skills", [])
    skills_text = ", ".join([f"{s['name']}:{s['level']}" for s in skills])
    
    # Xử lý hiển thị CCCD (tránh hiện chữ None)
    cccd_val = student.get('cccd')
    if cccd_val is None or str(cccd_val) == "None": 
        cccd_val = ""
        
    # Xử lý hiển thị Ngày sinh (cắt chuỗi ISO '2000-01-01T00:00:00' -> '2000-01-01')
    dob_raw = student.get('dob') 
    dob_val = dob_raw[:10] if dob_raw else "" 

    content = f"""
    <h2>👤 Thông tin cá nhân</h2>
    {message}
    <form method="post">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        
        <label>Họ tên <span style="color:red">*</span></label>
        <input name="fullName" value="{student.get('fullName','') or ''}" required>

        <div style="display:flex; gap:20px;">
            <div style="flex:1;">
                <label>Ngày sinh <span style="color:red">*</span></label>
                <input type="date" name="dob" value="{dob_val}" required>
            </div>
            <div style="flex:1;">
                <label>Số CCCD / CMND <span style="color:red">*</span></label>
                <input name="cccd" value="{cccd_val}" placeholder="Nhập số CCCD..." required>
            </div>
        </div>
        <label>Ngành học <span style="color:red">*</span></label>
        <input name="major" value="{student.get('major','') or ''}" required>
        
        <label>Giới thiệu bản thân</label>
        <textarea name="about" rows="3">{profile.get('about','') or ''}</textarea>
        
        <label>Trình độ học vấn </label>
        <input name="educationLevel" value="{profile.get('educationLevel','') or ''}">
        
        <label>Bằng cấp / Chứng chỉ</label>
        <input name="degrees" value="{profile.get('degrees','') or ''}">
        
        <label>Link CV (PDF/Drive) <span style="color:red">*</span></label>
        <input name="cvUrl" value="{profile.get('cvUrl','') or ''}" required>
        
        <label>Link Portfolio</label>
        <input name="portfolioUrl" value="{profile.get('portfolioUrl','') or ''}">
        
        <label>Kỹ năng (Định dạng: Tên:Level, VD: Python:5, Java:4)</label>
        <input name="skills" value="{skills_text}">
        
        <button style="margin-top:20px;">💾 Lưu hồ sơ</button>
    </form>
    """
    
    resp = make_response(wrap_layout(content))
    resp.set_cookie("csrf_token", csrf_token, httponly=True, samesite="Lax")
    return resp

@student_view_bp.route('/student/applications')
def student_applications():
    user = require_student_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]
    try:
        # 1. Lấy thông tin sinh viên
        stu_res = requests.get(
            f"{API_URL}/students/user/{user_id}",
            headers=auth_headers(),
            timeout=5
        )
        if stu_res.status_code != 200: 
            return wrap_layout(f"<h2>⚠️ Lỗi: Không tìm thấy sinh viên (API Code {stu_res.status_code})</h2>")
        
        student_data = stu_res.json()
        student_id = student_data['id']

        # 2. Lấy danh sách ứng tuyển (CODE DEBUG)
        app_url = f"{API_URL}/students/{student_id}/applications"
        app_res = requests.get(
            app_url,
            headers=auth_headers(),
            timeout=5
        )
        
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
        html = "<p><i>Chưa ứng tuyển công việc nào</i></p>"

    return wrap_layout(f"<h2>📌 Việc làm đã ứng tuyển</h2>{html}")

@student_view_bp.route("/student/tests/<int:job_id>")
def student_tests(job_id):
        
    user = require_student_view()
    if not user:
        return redirect('/login')
    
    user_id = user["id"]
    
    # 1. Lấy thông tin sinh viên
    stu_res = requests.get(f"{API_URL}/students/user/{user_id}", headers=auth_headers())
    if stu_res.status_code != 200:
        return redirect("/student/home?msg=❌+Lỗi+kết+nối+dữ+liệu+sinh+viên")
        
    stu = stu_res.json()

    # ==================================================================
    # 2. KIỂM TRA HỒ SƠ ĐẦY ĐỦ (BẮT BUỘC TRƯỚC KHI TEST)
    # ==================================================================
    required_fields = {
        "fullName": "Họ tên",
        "cccd": "CCCD",
        "major": "Ngành học"
    }
    
    missing = []
    
    # Kiểm tra thông tin cơ bản
    for field, label in required_fields.items():
        if not stu.get(field):
            missing.append(label)

    # Kiểm tra CV trong profile
    profile = stu.get("profile")
    if not profile or not profile.get("cvUrl"):
        missing.append("Link CV")

    # Nếu thiếu -> Chặn và đẩy về trang Profile
    if missing:
        missing_str = ", ".join(missing)
        msg = f"⚠️ Bạn cần cập nhật: {missing_str} để bắt đầu làm bài test!"
        return redirect(f"/student/profile?msg={msg}")
    # ==================================================================

    # 3. Hồ sơ OK -> Tiếp tục vào làm bài test
    student_id = stu["id"]
    start_res = requests.post(
        f"{API_URL}/tests/start",
        json={"jobId": job_id},
        headers=auth_headers()
    )
    if start_res.status_code in [200, 201]:
        test_id = start_res.json()["testId"]
        return redirect(f"/student/test/{test_id}")
        
    return redirect("/student/home")

@student_view_bp.route("/student/test/<int:test_id>")
def student_do_test(test_id):
    
    csrf_token = generate_csrf_token()

    user = require_student_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]

    # 1. Lấy thông tin sinh viên
    stu_res = requests.get(
        f"{API_URL}/students/user/{user_id}",
        headers=auth_headers(),
        timeout=5
    )
    if stu_res.status_code != 200:
        return wrap_layout("<p>❌ Không tìm thấy thông tin sinh viên</p>")

    student = stu_res.json()
    student_id = student["id"]

    # ==================================================================
    # 2. KIỂM TRA HỒ SƠ (BẮT BUỘC TRƯỚC KHI VÀO TRANG LÀM BÀI)
    # ==================================================================
    # Danh sách các trường cần kiểm tra
    # Lưu ý: API trả về None thì Python hiểu là None, nhưng khi hiển thị lên form có thể là chuỗi "None"
    # nên ta cần check kỹ cả 2 trường hợp.
    
    missing = []
    
    # Check Họ tên
    full_name = student.get("fullName")
    if not full_name or str(full_name).strip() == "" or str(full_name) == "None":
        missing.append("Họ tên")

    # Check CCCD
    cccd = student.get("cccd")
    if not cccd or str(cccd).strip() == "" or str(cccd) == "None":
        missing.append("CCCD")

    # Check Ngành học
    major = student.get("major")
    if not major or str(major).strip() == "" or str(major) == "None" or major == "Chưa cập nhật":
        missing.append("Ngành học")

    # Check Link CV (nằm trong profile)
    profile = student.get("profile")
    cv_url = profile.get("cvUrl") if profile else None
    if not cv_url or str(cv_url).strip() == "" or str(cv_url) == "None":
        missing.append("Link CV")

    # Nếu thiếu thông tin -> Đuổi về trang hồ sơ ngay
    if missing:
        msg = "Vui lòng nhập thông tin trước khi làm test: " + ", ".join(missing)
        return redirect(f"/student/profile?msg={msg}")
    # ==================================================================

    # 3. Nếu hồ sơ đủ -> Lấy đề thi hiển thị bình thường
    res = requests.get(f"{API_URL}/tests/{test_id}", headers=auth_headers())
    if res.status_code != 200:
        return wrap_layout("<p>❌ Không tìm thấy bài test hoặc bạn không có quyền truy cập</p>")

    test = res.json()
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
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        <input type="hidden" name="jobId" value="{test.get('jobId')}">
        {questions_html}
        <button type="submit" style="margin-top:20px; background:#2563eb; color:white; padding:10px 20px; border:none; border-radius:4px; cursor:pointer;">📤 Nộp bài test</button>
    </form>
    """
    
    resp = make_response(wrap_layout(content))
    resp.set_cookie("csrf_token", csrf_token, httponly=True, samesite="Lax")
    return resp


@student_view_bp.route("/student/test/submit/<int:test_id>", methods=["POST"])
def student_test_submit(test_id):
    # 1. CSRF
    if not validate_csrf(request.form.get("csrf_token")):
        return "CSRF token không hợp lệ", 400

    # 2. Auth bằng JWT (không session)
    user = require_student_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]

    # 3. Lấy studentId
    stu_res = requests.get(
        f"{API_URL}/students/user/{user_id}",
        headers=auth_headers(),
        timeout=5
    )
    if stu_res.status_code != 200:
        return redirect("/student/home?msg=❌+Không+tìm+thấy+sinh+viên")

    student_id = stu_res.json()["id"]

    # 4. Submit bài test
    answers = {
        k: v for k, v in request.form.items()
        if k not in ("csrf_token", "jobId")
    }

    
    submit_payload = {
        "studentId": student_id,
        "score": 0,
        "answers": answers
    }

    submit_res = requests.post(
        f"{API_URL}/tests/{test_id}/submit",
        json=submit_payload,
        headers=auth_headers()
    )
    if submit_res.status_code not in (200, 201):
        try:
            msg = submit_res.json().get("detail") or submit_res.text
        except:
            msg = submit_res.text
        return redirect(f"/student/home?msg=❌+Lỗi+nộp+bài:+{msg}")

    # 5. Apply job (jobId lấy từ form, KHÔNG session)
    job_id = request.form.get("jobId")
    if job_id:
        try:
            apply_res = requests.post(
                f"{API_URL}/apply/",
                json={"studentId": student_id, "jobId": int(job_id)},
                headers=auth_headers()
            )

            if apply_res.status_code in (200, 201):
                try:
                    data = apply_res.json()
                except:
                    data = {}

                if data.get("status") in ("ALREADY_APPLIED", "APPLIED"):
                    return redirect("/student/home?msg=✅+Hoàn+thành+bài+test+và+đã+ứng+tuyển")
                elif data.get("status") == "NEED_TEST":
                    return redirect("/student/home?msg=✅+Hoàn+thành+bài+test,+đang+chờ+xét+duyệt")
                else:
                    return redirect("/student/home?msg=✅+Hoàn+thành+bài+test")
            else:
                return redirect("/student/home?msg=⚠️+Hoàn+thành+bài+test+nhưng+apply+lỗi")

        except Exception:
            return redirect("/student/home?msg=⚠️+Hoàn+thành+bài+test+nhưng+apply+thất+bại")

    # 6. Không có jobId
    return redirect("/student/home?msg=✅+Hoàn+thành+bài+test")
