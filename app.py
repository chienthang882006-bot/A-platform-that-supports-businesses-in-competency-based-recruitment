from flask import Flask, request, session, redirect, url_for
import requests
import json  # [MỚI] Cần import json để xử lý dữ liệu câu hỏi

app = Flask(__name__)
app.secret_key = 'labodc_secret_key'
API_URL = "http://127.0.0.1:8000/api"


# ======================
# LAYOUT & NOTIFICATIONS
# ======================
def show_notifications():
    if 'user' not in session:
        return ""
    
    try:
        # Gọi API lấy thông báo
        res = requests.get(f"{API_URL}/notifications/{session['user']['id']}")
        
        count = 0
        list_html = ""

        if res.status_code == 200:
            notifs = res.json()
            count = len(notifs) # Đếm số lượng

            if count == 0:
                list_html = "<div class='notif-item'>Không có thông báo mới</div>"
            else:
                for n in notifs[:5]: # Chỉ lấy 5 tin mới nhất
                    list_html += f"""
                    <div class="notif-item">
                        <div class="notif-content">{n.get('content', 'Thông báo mới')}</div>
                        <div class="notif-time">{n.get('createdAt', '')[:10]}</div>
                    </div>
                    """
        
        badge_html = f'<span class="notif-badge">{count}</span>' if count > 0 else ''

        return f"""
        <div class="notif-wrapper">
            <div class="notif-bell" onclick="toggleNotif()">
                🔔 {badge_html}
            </div>
            <div id="notif-dropdown" class="notif-dropdown">
                <div class="notif-header">Thông báo</div>
                <div class="notif-list">
                    {list_html}
                </div>
            </div>
        </div>
        """
    except Exception as e:
        print(f"Lỗi notif: {e}")
        return ""

def wrap_layout(content):
    hide_sidebar = request.path in ['/auth', '/login', '/register']
    notif_html = show_notifications()

    if 'user' in session and not hide_sidebar:
        user = session['user']
        
        menu = ""
        if user['role'] == 'student':
            menu = """
            <a href="/student/home">🏠 Trang chủ</a>
            <a href="/student/profile">👤 Hồ sơ</a>
            <a href="/student/applications">📌 Đã ứng tuyển</a>
            """
        elif user['role'] == 'company':
            menu = """
            <a href="/company/home">🏢 Dashboard</a>
            <a href="/company/jobs">📄 Quản lý Job</a>
            <a href="/company/applications">📥 Ứng viên</a>
            """

        sidebar = f"""
        <div class="sidebar">
            <div class="profile">
                <div class="email">{user['email']}</div>
                <div class="role">{user['role']}</div>
            </div>
            <div class="menu">
                {menu}
                <a href="/logout">🚪 Đăng xuất</a>
            </div>
        </div>
        """
    else:
        sidebar = ""

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>LabOdc Recruitment</title>

        <style>
            /* ===== BASIC STYLES ===== */
            body {{ margin: 0; font-family: Arial, sans-serif; background: #f0f2f5; }}
            
            /* APP BAR */
            .app-bar {{
                position: fixed; top: 0; left: 0; right: 0; height: 60px;
                background: white; display: flex; align-items: center; justify-content: space-between;
                padding: 0 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); z-index: 1000;
            }}
            .app-title {{ font-size: 22px; font-weight: bold; color: #0f172a; text-decoration: none; }}

            /* NOTIFICATIONS */
            .notif-wrapper {{ position: relative; margin-right: 20px; }}
            .notif-bell {{ font-size: 24px; cursor: pointer; position: relative; user-select: none; padding: 5px; }}
            .notif-badge {{
                position: absolute; top: 0; right: -5px; background: red; color: white; 
                font-size: 11px; padding: 2px 6px; border-radius: 10px; font-weight: bold; border: 2px solid white;
            }}
            .notif-dropdown {{
                display: none; position: absolute; top: 50px; right: 0; width: 300px; 
                background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
                z-index: 2000; border: 1px solid #eee;
            }}
            .notif-header {{ background: #f8fafc; padding: 10px 15px; font-weight: bold; border-bottom: 1px solid #eee; font-size: 14px; }}
            .notif-list {{ max-height: 300px; overflow-y: auto; }}
            .notif-item {{ padding: 12px 15px; border-bottom: 1px solid #f1f1f1; font-size: 13px; color: #333; }}
            .notif-item:hover {{ background: #f8fafc; }}
            .notif-time {{ font-size: 11px; color: #94a3b8; margin-top: 4px; }}
            .notif-show {{ display: block; }}

            /* SIDEBAR & MAIN */
            .sidebar {{
                position: fixed; top: 60px; left: 0; width: 220px; height: calc(100vh - 60px);
                background: #0f172a; color: white; padding: 20px 15px; box-sizing: border-box;
            }}
            .profile {{ text-align: center; margin-bottom: 30px; }}
            .email {{ font-size: 13px; word-break: break-all; }}
            .role {{ font-size: 12px; color: #94a3b8; margin-top: 4px; }}
            .menu a {{
                display: block; padding: 10px 12px; margin-bottom: 6px;
                border-radius: 8px; text-decoration: none; color: #e5e7eb; font-size: 14px;
            }}
            .menu a:hover {{ background: #1e293b; }}
            .main {{
                margin-left: 220px; margin-top: 60px; padding: 30px;
                min-height: calc(100vh - 60px); background: white; box-sizing: border-box;
            }}
            .no-sidebar .main {{ margin-left: 0; }}

            /* UI ELEMENTS */
            .job-card {{
                border-left: 6px solid #ff4b4b; padding: 15px; margin: 15px 0;
                background: #fafafa; border-radius: 8px;
            }}
            label {{ font-weight: bold; margin-top: 12px; display: block; }}
            input, select, textarea {{
                width: 100%; padding: 10px; margin: 8px 0;
                border-radius: 5px; border: 1px solid #ddd;
            }}
            button {{
                background: #2563eb; color: white; padding: 10px; border: none;
                width: 100%; border-radius: 6px; cursor: pointer; font-size: 14px;
            }}
            button:hover {{ background: #1e40af; }}
        </style>
    </head>

    <body class="{ 'no-sidebar' if hide_sidebar else '' }">
        <div class="app-bar">
            <a href="/student/home" class="app-title">🚀 LabOdc Recruitment</a>
            {notif_html} 
        </div>

        {sidebar}

        <div class="main">
            {content}
        </div>

        <script>
            function toggleNotif() {{
                var dropdown = document.getElementById("notif-dropdown");
                if (dropdown) {{ dropdown.classList.toggle("notif-show"); }}
            }}
            window.onclick = function(event) {{
                if (!event.target.matches('.notif-bell') && !event.target.matches('.notif-bell *')) {{
                    var dropdowns = document.getElementsByClassName("notif-dropdown");
                    for (var i = 0; i < dropdowns.length; i++) {{
                        var openDropdown = dropdowns[i];
                        if (openDropdown.classList.contains('notif-show')) {{
                            openDropdown.classList.remove('notif-show');
                        }}
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """

# ======================
# AUTH ROUTES
# ======================
@app.route('/')
def index():
    return redirect('/auth')

@app.route('/auth')
def auth():
    return wrap_layout("""
    <h2>🔐 Xác thực người dùng</h2>
    <p>Vui lòng chọn chức năng:</p>
    <div style="display:flex; gap:20px; margin-top:20px;">
        <a href="/login" style="flex:1; text-align:center; padding:15px; background:#2563eb; color:white; border-radius:8px; text-decoration:none; font-weight:bold;">🔑 Đăng nhập</a>
        <a href="/register" style="flex:1; text-align:center; padding:15px; background:#16a34a; color:white; border-radius:8px; text-decoration:none; font-weight:bold;">📝 Đăng ký</a>
    </div>
    """)

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""
    if request.method == 'POST':
        payload = {
            "email": request.form['email'],
            "password": request.form['password'],
            "role": request.form['role']
        }
        try:
            res = requests.post(f"{API_URL}/users/", json=payload)
            if res.status_code in [200, 201]:
                message = "✅ Đăng ký thành công"
            else:
                message = res.json().get("detail", "Lỗi")
        except Exception as e:
            message = f"❌ Lỗi backend: {e}"

    return wrap_layout(f"""
    <h2>📝 Đăng ký</h2>
    <p>{message}</p>
    <form method="post">
        <input name="email" placeholder="Email" required>
        <input name="password" type="password" placeholder="Mật khẩu" required>
        <select name="role">
            <option value="student">Sinh viên</option>
            <option value="company">Doanh nghiệp</option>
        </select>
        <button>Đăng ký</button>
    </form>
    """)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        try:
            res = requests.post(f"{API_URL}/login/", json={
                "email": request.form['email'],
                "password": request.form['password']
            })
            if res.status_code == 200:
                user = res.json()
                session['user'] = user
                if user['role'] == 'student': return redirect('/student/home')
                elif user['role'] == 'company': return redirect('/company/home')
                elif user['role'] == 'admin': return redirect('/admin/dashboard')
            else:
                message = "Sai tài khoản hoặc mật khẩu"
        except:
            message = "Lỗi backend"

    return wrap_layout(f"""
    <h2>🔑 Đăng nhập</h2>
    <p>{message}</p>
    <form method="post">
        <input name="email" placeholder="Email" required>
        <input name="password" type="password" placeholder="Mật khẩu" required>
        <button>Đăng nhập</button>
    </form>
    """)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/auth')


# ======================
# STUDENT ROUTES
# ======================
@app.route("/student/home")
def student_home():
    if "user" not in session or session["user"]["role"] != "student":
        return redirect("/login")

    message = session.pop("apply_message", "")
    jobs = []
    applied_job_ids = []
    done_test_ids = []

    try:
        # 1) Lấy student trước (bắt buộc để gọi /jobs?studentId=)
        user_id = session['user']['id']
        stu_res = requests.get(f"{API_URL}/students/user/{user_id}", timeout=5)
        if stu_res.status_code != 200:
            # Không có student -> show message
            return wrap_layout("<p>⚠️ Không tìm thấy hồ sơ sinh viên</p>")
        stu = stu_res.json()
        student_id = stu["id"]

        # 2) Gọi API jobs kèm studentId để backend lọc job đã apply (nếu backend hỗ trợ)
        try:
            res = requests.get(f"{API_URL}/jobs/", params={"studentId": student_id}, timeout=5)
            jobs = res.json() if res.status_code == 200 else []
        except Exception:
            # fallback: lấy toàn bộ jobs nếu request bị lỗi
            res = requests.get(f"{API_URL}/jobs/", timeout=5)
            jobs = res.json() if res.status_code == 200 else []

        # 3) Lấy danh sách application (fallback/đối chiếu)
        applied_res = requests.get(f"{API_URL}/students/{student_id}/applications", timeout=5)
        if applied_res.status_code == 200:
            applied_job_ids = [a["jobId"] for a in applied_res.json()]
        # 4) Lấy danh sách test đã làm
        test_done_res = requests.get(f"{API_URL}/students/{student_id}/tests", timeout=5)
        if test_done_res.status_code == 200:
            done_test_ids = [t["testId"] for t in test_done_res.json()]

    except Exception as e:
        # Nếu có lỗi mạng/exception, hiển thị rỗng nhưng không crash
        print("Error loading student/home data:", e)
        jobs = []

    # Build content
    content = f"<h2>💼 Danh sách việc làm</h2><p>{message}</p>"

    for j in jobs:
        job_id = j.get("id")
        has_test = j.get("hasTest", False)
        test_id = j.get("testId", None)

        # Nếu backend đã lọc applied nhưng frontend có fallback list -> tránh hiển thị
        if job_id in applied_job_ids:
            continue

        # Nếu job đã đóng (nếu backend vẫn trả Closed), skip
        if str(j.get("status", "")).upper() == "CLOSED":
            continue

        # 1) Có test nhưng chưa làm -> show nút làm test
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
        # 2) Không test hoặc đã làm test -> cho apply
        else:
            content += f"""
            <div class="job-card">
                <h3>{j.get('title','(No title)')}</h3>
                <p>{j.get('description','')}</p>
                <form method="post" action="/apply/{job_id}">
                    <button>✅ Ứng tuyển</button>
                </form>
            </div>
            """

    return wrap_layout(content)



@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
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
        # 🔥 JOB CÓ TEST
        if data.get("status") == "NEED_TEST":
            session["current_job_id"] = job_id   # ⭐ BẮT BUỘC
            return redirect(f"/student/test/{data['testId']}")
        # 🔥 JOB KHÔNG CÓ TEST
        if data.get("status") == "APPLIED":
            session["apply_message"] = "✅ Ứng tuyển thành công"
            return redirect("/student/home")
    session["apply_message"] = "❌ Không thể ứng tuyển"
    return redirect("/student/home")




@app.route("/student/profile", methods=["GET", "POST"])
def student_profile():
    if 'user' not in session:
        return redirect('/login')
    user_id = session['user']['id']
    # ===== LẤY STUDENT + PROFILE + SKILLS =====
    stu_res = requests.get(f"{API_URL}/students/user/{user_id}")
    if stu_res.status_code != 200:
        return wrap_layout("<p>⚠️ Không tìm thấy hồ sơ sinh viên</p>")
    student = stu_res.json()
    student_id = student["id"]
    profile = student.get("profile") or {}
    skills = student.get("skills", [])
    skills_text = ", ".join([f"{s['name']}:{s['level']}" for s in skills])
    message = ""
    # ===== LƯU HỒ SƠ =====
    if request.method == "POST":
        # --- parse kỹ năng ---
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
            # students
            "fullName": request.form.get("fullName"),
            "major": request.form.get("major"),
            # student_profiles
            "about": request.form.get("about"),
            "educationLevel": request.form.get("educationLevel"),
            "degrees": request.form.get("degrees"),
            "cvUrl": request.form.get("cvUrl"),
            "portfolioUrl": request.form.get("portfolioUrl"),
            # ⭐ KỸ NĂNG
            "skills": skills_list
        }
        res = requests.put(
            f"{API_URL}/students/{student_id}",
            json=payload
        )
        if res.status_code == 200:
            message = "<p style='color:green;'>✅ Hồ sơ đã được lưu</p>"
            # reload data
            student = requests.get(f"{API_URL}/students/user/{user_id}").json()
            profile = student.get("profile") or {}
            skills = student.get("skills", [])
            skills_text = ", ".join([f"{s['name']}:{s['level']}" for s in skills])
        else:
            message = "<p style='color:red;'>❌ Lưu hồ sơ thất bại</p>"

    # ===== FORM HIỂN THỊ =====
    content = f"""
    <h2>👤 Thông tin cá nhân</h2>
    {message}
    <form method="post">
        <label>Họ tên</label>
        <input name="fullName" value="{student.get('fullName','')}">

        <label>Ngành học</label>
        <input name="major" value="{student.get('major','')}">

        <label>Giới thiệu</label>
        <textarea name="about">{profile.get('about','')}</textarea>

        <label>Trình độ học vấn</label>
        <input name="educationLevel" value="{profile.get('educationLevel','')}">

        <label>Bằng cấp</label>
        <input name="degrees" value="{profile.get('degrees','')}">

        <label>Link CV</label>
        <input name="cvUrl" value="{profile.get('cvUrl','')}">

        <label>Portfolio</label>
        <input name="portfolioUrl" value="{profile.get('portfolioUrl','')}">

        <label>Kỹ năng </label>
        <input name="skills" value="{skills_text}">

        <button>💾 Lưu hồ sơ</button>
    </form>
    """
    return wrap_layout(content)


@app.route('/student/applications')
def student_applications():
    if 'user' not in session: return redirect('/login')
    content = "<h2>📌 Việc làm đã ứng tuyển</h2>"
    try:
        user_id = session['user']['id']
        stu = requests.get(f"{API_URL}/students/user/{user_id}").json()
        apps = requests.get(f"{API_URL}/students/{stu['id']}/applications").json()
        for a in apps:
            content += f"""
            <div class="job-card">
                <b>{a['jobTitle']}</b><br>
                Trạng thái: {a['status']}
            </div>
            """
    except:
        content += "<p>Lỗi tải dữ liệu</p>"
    return wrap_layout(content)


@app.route("/student/tests/<int:job_id>")
def student_tests(job_id):
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect('/login')
    session["current_job_id"] = job_id
    user_id = session['user']['id']
    stu = requests.get(f"{API_URL}/students/user/{user_id}").json()
    student_id = stu["id"]
    # 👉 GỌI START TEST (BACKEND)
    start_res = requests.post(
        f"{API_URL}/tests/start",
        json={"studentId": student_id, "jobId": job_id}
    )
    if start_res.status_code in [200, 201]:
        test_id = start_res.json()["testId"]
        return redirect(f"/student/test/{test_id}")
    return redirect("/student/home")


@app.route("/student/test/<int:test_id>")
def student_do_test(test_id):
    if 'user' not in session:
        return redirect('/login')
    # Lấy student id
    user_id = session['user']['id']
    stu_res = requests.get(f"{API_URL}/students/user/{user_id}")
    if stu_res.status_code != 200:
        return wrap_layout("<p>❌ Không tìm thấy sinh viên</p>")
    student_id = stu_res.json()["id"]
    # 1) Lấy test detail (chứa jobId)
    res = requests.get(f"{API_URL}/tests/{test_id}")
    if res.status_code != 200:
        return wrap_layout("<p>❌ Không tìm thấy bài test</p>")
    test = res.json()
    job_id = test.get("jobId")
    # 2) Nếu session chưa có current_job_id, dùng jobId từ test
    if not session.get("current_job_id") and job_id:
        session["current_job_id"] = job_id

    job_to_start = session.get("current_job_id") or job_id
    if not job_to_start:
        return wrap_layout("<p>❌ Bài test chưa liên kết với job</p>")
    # 3) Gọi start (tạo TestResult nếu chưa có)
    start_res = requests.post(
        f"{API_URL}/tests/start",
        json={"studentId": student_id, "jobId": job_to_start}
    )
    if start_res.status_code not in [200, 201]:
        # show backend message để debug
        try:
            msg = start_res.json().get("detail") or start_res.text
        except:
            msg = start_res.text
        return wrap_layout(f"<p>❌ Không thể bắt đầu bài test: {msg}</p>")
    # 4) Render form (kèm hidden jobId để an toàn)
    questions_html = ""
    for idx, q in enumerate(test.get("questions", []), start=1):
        questions_html += f"""
        <div class="job-card">
            <b>Câu {idx}:</b> {q['content']}<br>
            <input type="text" name="answer_{q['id']}" placeholder="Nhập câu trả lời của bạn" required>
        </div>
        """
    content = f"""
    <h2>📝 {test.get('testName')}</h2>
    <p>⏱ Thời gian: {test.get('duration')} phút</p>
    <form method="post" action="/student/test/submit/{test_id}">
        <input type="hidden" name="jobId" value="{job_to_start}">
        {questions_html}
        <button type="submit">📤 Nộp bài test</button>
    </form>
    """
    return wrap_layout(content)


@app.route("/student/test/submit/<int:test_id>", methods=["POST"])
def student_test_submit(test_id):
    if 'user' not in session:
        return redirect('/login')
    # Lấy student id
    user_id = session['user']['id']
    stu_res = requests.get(f"{API_URL}/students/user/{user_id}")
    if stu_res.status_code != 200:
        session["apply_message"] = "❌ Lỗi: không tìm thấy sinh viên"
        return redirect("/student/home")
    student_id = stu_res.json()["id"]
    # Thu câu trả lời (nếu cần gửi lên backend)
    answers = dict(request.form)
    # 1) Submit kết quả test
    submit_payload = {
        "studentId": student_id,
        "score": 0,       # nếu bạn chấm ở client thì gửi score phù hợp
        "answers": answers
    }
    submit_res = requests.post(f"{API_URL}/tests/{test_id}/submit", json=submit_payload)
    if submit_res.status_code not in (200, 201):
        # show backend lỗi
        try:
            msg = submit_res.json().get("detail") or submit_res.text
        except:
            msg = submit_res.text
        session["apply_message"] = f"❌ Lỗi nộp bài: {msg}"
        return redirect("/student/home")
    # 2) Sau khi submit test thành công → cố gắng apply (nếu chưa apply)
    job_id = session.pop("current_job_id", None) or request.form.get("jobId")
    if job_id:
        try:
            apply_res = requests.post(
                f"{API_URL}/apply/",
                json={"studentId": student_id, "jobId": int(job_id)}
            )
            # 200/201: đã apply thành công hoặc đã có application trước đó
            if apply_res.status_code in (200, 201):
                data = {}
                try:
                    data = apply_res.json()
                except:
                    data = {}
                # Nếu backend trả ALREADY_APPLIED hoặc APPLIED/NEED_TEST -> thông báo tương ứng
                if data.get("status") in ("ALREADY_APPLIED", "APPLIED"):
                    session["apply_message"] = "✅ Hoàn thành bài test & đã ứng tuyển"
                elif data.get("status") == "NEED_TEST":
                    # trường hợp hiếm: backend yêu cầu test tiếp (chưa xảy ra), coi là success
                    session["apply_message"] = "✅ Hoàn thành bài test, hồ sơ đang chờ xét duyệt"
                else:
                    session["apply_message"] = "✅ Hoàn thành bài test"
            else:
                # có lỗi khi apply -> vẫn thông báo test ok nhưng kèm cảnh báo
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


# ======================
# COMPANY ROUTES
# ======================
@app.route('/company/home')
def company_home():
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')
    content = f"""
    <h2>🏢 Dashboard Doanh nghiệp</h2>
    <p>Xin chào <b>{session['user']['email']}</b></p>
    <div class="job-card">
        <h3>📄 Quản lý tin tuyển dụng</h3>
        <a href="/company/jobs">Xem danh sách job</a>
    </div>
    <div class="job-card">
        <h3>📥 Hồ sơ ứng tuyển</h3>
        <a href="/company/applications">Xem ứng viên</a>
    </div>
    """
    return wrap_layout(content)


@app.route('/company/jobs')
def company_jobs():
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')
    user_id = session['user']['id']
    content = "<h2>📄 Tin tuyển dụng của công ty</h2>"
    try:
        # Lấy thông tin công ty
        comp_res = requests.get(f"{API_URL}/companies/user/{user_id}")
        if comp_res.status_code != 200:
            return wrap_layout("<h2>⚠️ Chưa có hồ sơ công ty</h2>")      
        company = comp_res.json()       
        # [CẬP NHẬT] Gọi API lấy Job CỦA RIÊNG CÔNG TY để đảm bảo tính chính xác
        jobs_res = requests.get(f"{API_URL}/companies/{company['id']}/jobs")
        my_jobs = jobs_res.json() if jobs_res.status_code == 200 else []
    except Exception as e:
        return wrap_layout(f"<p>❌ Lỗi kết nối: {e}</p>")
    content += """
    <a href="/company/jobs/create" style="display:inline-block; margin:10px 0; padding:10px 14px; background:#16a34a; color:white; border-radius:6px; text-decoration:none; font-weight:bold;">
        ➕ Tạo Job mới
    </a>
    """
    if not my_jobs:
        content += "<p>Chưa có tin tuyển dụng nào.</p>"
    for j in my_jobs:
        content += f"""
        <div class="job-card">
            <h3>{j['title']}</h3>
            <p style="white-space: pre-line; color:#555;">{j['description']}</p>
            <!-- ⭐ HIỂN THỊ TỔNG SỐ ỨNG VIÊN -->
            <p><b>Ứng viên:</b> {j.get('appliedCount', 0)} / {j.get('maxApplicants', '∞')}</p>       
            <div style="margin-top:15px; border-top:1px solid #eee; padding-top:10px;">
                <a href="/company/jobs/{j['id']}/edit" style="margin-right:15px; color:#f59e0b; font-weight:bold; text-decoration:none;">
                    ✏️ Chỉnh sửa
                </a>
                <a href="/company/jobs/{j['id']}/applications" style="color:#16a34a; font-weight:bold; text-decoration:none;">
                    📥 Xem ứng viên
                </a>
            </div>
        </div>
        """
    return wrap_layout(content)


@app.route('/company/jobs/create', methods=['GET', 'POST'])
def company_create_job():
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')
    message = ""
    if request.method == 'POST':
        try:
            # 1. Lấy thông tin công ty
            comp_res = requests.get(f"{API_URL}/companies/user/{session['user']['id']}")
            company = comp_res.json()
            # 2. Đóng gói payload cơ bản cho Job
            payload = {
                "companyId": company['id'],
                "title": request.form['title'],
                "description": request.form['description'],
                "location": request.form['location'],
                "status": "open",
                "maxApplicants": int(request.form.get("maxApplicants"))
            }
            # 3. Xử lý bài Test nếu được tích chọn
            if request.form.get('has_test') == 'on':
                q_contents = request.form.getlist('q_content[]')
                q_options = request.form.getlist('q_options[]')
                q_answers = request.form.getlist('q_answer[]')
                questions = []
                for c, o, a in zip(q_contents, q_options, q_answers):
                    if c.strip():
                        # Đóng gói từng câu hỏi theo đúng cấu trúc Backend mong đợi
                        questions.append({
                            "content": c,
                            "options": o, 
                            "correctAnswer": a
                        })              
                payload["test"] = {
                    "testName": request.form.get('testName', f"Test for {payload['title']}"),
                    "duration": int(request.form.get('duration') or 30),
                    "totalScore": int(request.form.get('totalScore') or 100),
                    "questions": questions
                }
            # 4. Gửi yêu cầu POST tới Backend
            res = requests.post(f"{API_URL}/jobs/", json=payload)      
            if res.status_code in [200, 201]:
                return redirect('/company/jobs') 
            else:
                message = f"❌ Lỗi Backend: {res.text}"
        except Exception as e:
            message = f"❌ Lỗi xử lý: {e}"
    
    return wrap_layout(f"""
    <h2>📄 Tạo tin tuyển dụng</h2>
    <p style="color:red; font-weight:bold;">{message}</p>
    <form method="post">
        <div class="job-card">
            <h3>Thông tin công việc</h3>
            <label>Tiêu đề</label>
            <input name="title" required>
            <label>Mô tả</label>
            <textarea name="description" required></textarea>
            <label>Địa điểm</label>
            <input name="location">
            <label>Số ứng viên tối đa</label>
            <input name="maxApplicants" type="number" min="1" placeholder="Ví dụ: 10">
        </div>
        <div class="job-card" style="border-left: 6px solid #2563eb; background:#f8fafc;">
            <label style="display:flex; align-items:center; cursor:pointer; color:#2563eb;">
                <input type="checkbox" name="has_test" id="chkTest" onclick="toggleTestForm()" style="width:auto; margin-right:10px;">
                <b>Kèm bài kiểm tra năng lực?</b>
            </label>
            <div id="test-form" style="display:none; margin-top:15px; border-top:1px solid #ddd; padding-top:10px;">
                <label>Tên bài kiểm tra</label>
                <input name="testName">
                <div style="display:flex; gap:15px;">
                    <div style="flex:1;"><label>Thời gian (phút)</label><input type="number" name="duration" value="30"></div>
                    <div style="flex:1;"><label>Tổng điểm</label><input type="number" name="totalScore" value="100"></div>
                </div>
                <label>Danh sách câu hỏi:</label>
                <div id="questions-container"></div>
                <button type="button" onclick="addQuestion()" style="background:#475569; width:auto; padding:8px 15px; margin-top:10px;">+ Thêm câu hỏi</button>
            </div>
        </div>
        <button style="margin-top:20px;">➕ Tạo Job</button>
    </form>
    <script>
        function toggleTestForm() {{
            var chk = document.getElementById("chkTest");
            var form = document.getElementById("test-form");
            form.style.display = chk.checked ? "block" : "none";
            if(chk.checked && document.getElementById("questions-container").innerHTML === "") addQuestion();
        }}
        function addQuestion() {{
            var div = document.createElement("div");
            div.style.marginBottom = "10px"; div.style.padding = "10px"; div.style.background = "white"; div.style.border = "1px solid #ddd";
            div.innerHTML = `<div style="font-weight:bold; font-size:13px; margin-bottom:5px;">Câu hỏi mới</div><input name="q_content[]" placeholder="Nội dung..." required style="margin-bottom:5px;"><input name="q_options[]" placeholder="Đáp án..." required style="margin-bottom:5px;"><input name="q_answer[]" placeholder="Đáp án đúng..." required><button type="button" onclick="this.parentElement.remove()" style="background:#ef4444; width:auto; padding:4px 10px; font-size:12px; margin-top:5px;">Xóa</button>`;
            document.getElementById("questions-container").appendChild(div);
        }}
    </script>
    """)

# [MỚI] HÀM CHỈNH SỬA JOB (THAY THẾ CHO CREATE TEST RIÊNG LẺ)
@app.route('/company/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def company_edit_job(job_id):
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')
    user_id = session['user']['id']
    message = ""    
    try:
        comp = requests.get(f"{API_URL}/companies/user/{user_id}").json()
        company_id = comp['id']
        job_res = requests.get(f"{API_URL}/jobs/{job_id}")
        if job_res.status_code != 200: return wrap_layout("<h2>❌ Không tìm thấy Job</h2>")
        job = job_res.json()
        if job.get('companyId') != company_id: return wrap_layout("<h2>⛔ Bạn không có quyền</h2>")       
        test_res = requests.get(f"{API_URL}/jobs/{job_id}/tests")
        tests = test_res.json() if test_res.status_code == 200 else []
        current_test = tests[0] if tests else None
        test_questions = []
        if current_test:
             q_res = requests.get(f"{API_URL}/tests/{current_test['id']}")
             if q_res.status_code == 200: test_questions = q_res.json().get('questions', [])
    except Exception as e:
        return wrap_layout(f"<h2>❌ Lỗi tải dữ liệu: {e}</h2>")
    if request.method == 'POST':
        try:
            payload = {
                "companyId": company_id,
                "title": request.form['title'],
                "description": request.form['description'],
                "location": request.form['location'],
                "maxApplicants": int(request.form.get("maxApplicants"))
            }
            if request.form.get('has_test') == 'on':
                q_contents = request.form.getlist('q_content[]')
                q_options = request.form.getlist('q_options[]')
                q_answers = request.form.getlist('q_answer[]')
                questions_list = []
                for c, o, a in zip(q_contents, q_options, q_answers):
                    if c.strip(): questions_list.append({"content": c, "options": o, "correctAnswer": a})
                payload["test"] = {
                    "testName": request.form['testName'],
                    "duration": int(request.form['duration'] or 30),
                    "totalScore": int(request.form['totalScore'] or 100),
                    "questions": questions_list
                }
            res = requests.put(f"{API_URL}/jobs/{job_id}", json=payload)
            if res.status_code == 200: return redirect('/company/jobs')
            else: message = f"❌ Lưu thất bại: {res.text}"
        except Exception as e:
            message = f"❌ Lỗi xử lý: {e}"

    questions_json = json.dumps(test_questions) if current_test else "[]"
    has_test_checked = "checked" if current_test else ""
    display_test_form = "block" if current_test else "none"

    return wrap_layout(f"""
    <h2>✏️ Chỉnh sửa tin tuyển dụng</h2>
    <p style="color:red">{message}</p>
    <a href="/company/jobs">← Quay lại danh sách</a>
    <form method="post" style="margin-top:20px;">
        <div class="job-card">
            <h3>Thông tin công việc</h3>
            <label>Tiêu đề</label><input name="title" required value="{job['title']}">
            <label>Mô tả</label><textarea name="description" required style="min-height:120px;">{job['description']}</textarea>
            <label>Địa điểm</label><input name="location" value="{job.get('location', '')}">
        </div>
        <div class="job-card" style="border-left: 6px solid #2563eb; background:#f0f9ff;">
            <label style="display:flex; align-items:center; cursor:pointer; color:#2563eb; margin-bottom:15px;">
                <input type="checkbox" name="has_test" id="chkTest" onclick="toggleTestForm()" {has_test_checked} style="width:auto; margin-right:10px;"><b>Kèm bài kiểm tra năng lực?</b>
            </label>
            <div id="test-form" style="display:{display_test_form};">
                <label>Tên bài kiểm tra</label><input name="testName" value="{current_test.get('testName', '') if current_test else ''}">
                <div style="display:flex; gap:15px;">
                    <div style="flex:1;"><label>Thời gian</label><input type="number" name="duration" value="{current_test.get('duration', 30) if current_test else 30}"></div>
                    <div style="flex:1;"><label>Tổng điểm</label><input type="number" name="totalScore" value="{current_test.get('totalScore', 100) if current_test else 100}"></div>
                </div>
                <h4 style="margin-top:20px;">Danh sách câu hỏi:</h4>
                <div id="questions-container"></div>
                <button type="button" onclick="addQuestionInput()" style="background:#475569; margin-top:15px; width:auto; padding:8px 15px; font-size:13px;">+ Thêm câu hỏi</button>
            </div>
        </div>
        <button style="margin-top:20px; padding:12px; font-size:16px; background:#f59e0b;">💾 Lưu thay đổi</button>
    </form>
    <script>
        var existingQuestions = {questions_json};
        function toggleTestForm() {{
            var chk = document.getElementById("chkTest");
            document.getElementById("test-form").style.display = chk.checked ? "block" : "none";
        }}
        function addQuestionInput(content='', options='', answer='') {{
            var container = document.getElementById("questions-container");
            var div = document.createElement("div");
            div.style.marginBottom = "15px"; div.style.padding = "15px"; div.style.background = "white"; div.style.border = "1px solid #cbd5e1";
            div.innerHTML = `<div style="font-weight:bold; font-size:13px; margin-bottom:8px;">Câu hỏi</div><input name="q_content[]" placeholder="Nội dung..." required value="${{content}}" style="margin-bottom:8px;"><div style="display:flex; gap:10px;"><div style="flex:2;"><input name="q_options[]" placeholder="Đáp án..." required value="${{options}}"></div><div style="flex:1;"><input name="q_answer[]" placeholder="Đáp án đúng..." required value="${{answer}}"></div></div><button type="button" onclick="this.parentElement.remove()" style="background:#ef4444; width:auto; padding:4px 10px; font-size:11px; margin-top:5px;">Xóa</button>`;
            container.appendChild(div);
        }}
        window.onload = function() {{
            if (existingQuestions.length > 0) {{ existingQuestions.forEach(q => {{ addQuestionInput(q.content.replace(/"/g, '&quot;'), q.options.replace(/"/g, '&quot;'), q.correctAnswer); }}); }}
            else if (document.getElementById("chkTest").checked) {{ addQuestionInput(); }}
        }};
    </script>
    """)

@app.route('/company/applications')
def company_applications():
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')

    try:
        user_id = session['user']['id']
        comp_res = requests.get(f"{API_URL}/companies/user/{user_id}")
        company = comp_res.json()
        apps_res = requests.get(f"{API_URL}/companies/{company['id']}/applications")
        apps = apps_res.json() if apps_res.status_code == 200 else []
    except:
        apps = []

    content = "<h2>📥 Danh sách hồ sơ ứng tuyển</h2>"
    if not apps:
        content += "<p style='color:#666;'>Chưa có hồ sơ nào.</p>"
    else:
        content += """<table style="width:100%; border-collapse:collapse; background:white; margin-top:20px;">
            <thead style="background:#f1f5f9; border-bottom:2px solid #e2e8f0;"><tr><th style="padding:15px; text-align:left;">Ứng viên</th><th style="padding:15px; text-align:left;">Vị trí</th><th style="padding:15px;">Điểm</th><th style="padding:15px;">Trạng thái</th><th style="padding:15px; text-align:right;">Hành động</th></tr></thead><tbody>"""
        for a in apps:
            score_display = f"<b>{a['testScore']}</b>" if a['testScore'] != "N/A" else "--"
            content += f"""<tr style="border-bottom:1px solid #eee;"><td style="padding:15px;"><b>{a['studentName']}</b></td><td style="padding:15px;">{a['jobTitle']}</td><td style="padding:15px;">{score_display}</td><td style="padding:15px;">{a['status']}</td><td style="padding:15px; text-align:right;"><a href="{a['cvUrl']}" target="_blank" style="margin-right:10px;">CV</a><a href="/company/applications/{a['applicationId']}/evaluate" style="background:#0f172a; color:white; padding:5px 10px; border-radius:4px; text-decoration:none;">Đánh giá</a></td></tr>"""
        content += "</tbody></table>"
    return wrap_layout(content)

@app.route('/company/applications/<int:app_id>/evaluate', methods=['GET', 'POST'])
def company_evaluate_application(app_id):
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')

    message = ""
    if request.method == 'POST':
        action = request.form.get('action')
        payload = {
            "skillScore": int(request.form.get('skillScore', 0)),
            "peerReview": request.form.get('peerReview'),
            "improvement": request.form.get('improvement'),
            "nextStatus": action
        }
        try:
            res = requests.post(f"{API_URL}/applications/{app_id}/evaluate", json=payload)
            if res.status_code in [200, 201]: return redirect('/company/applications')
            else: message = "❌ Lỗi khi cập nhật đánh giá"
        except: message = "❌ Lỗi kết nối server"

    return wrap_layout(f"""
    <h2>⚖️ Đánh giá & Phỏng vấn</h2>
    <p><a href="/company/applications">← Quay lại danh sách</a></p>
    <p style="color:red">{message}</p>
    <div class="job-card" style="border-left:6px solid #8b5cf6;">
        <h3>Hồ sơ #{app_id}</h3>
        <form method="post">
            <label>Điểm kỹ năng</label><input type="number" name="skillScore">
            <label>Nhận xét</label><textarea name="peerReview"></textarea>
            <label>Cải thiện</label><textarea name="improvement"></textarea>
            <div style="margin-top:20px; display:flex; gap:10px;">
                <button name="action" value="interview" style="background:#2563eb;">📅 Duyệt / Phỏng vấn</button>
                <button name="action" value="rejected" style="background:#ef4444;">❌ Từ chối</button>
            </div>
        </form>
    </div>
    """)

@app.route('/company/jobs/<int:job_id>/applications')
def company_view_applicants(job_id):
    if 'user' not in session or session['user']['role'] != 'company': return redirect('/login')
    try: apps = requests.get(f"{API_URL}/jobs/{job_id}/applications").json()
    except: apps = []
    content = f"<h2>📥 Ứng viên cho Job #{job_id}</h2>"
    for a in apps:
        content += f"""<div class="job-card"><b>{a['studentName']}</b><br>Trạng thái: {a['status']}<br><a href="{a['cvUrl']}" target="_blank">📄 Xem CV</a></div>"""
    return wrap_layout(content)

# ======================
# RUN APP
# ======================
if __name__ == '__main__':
    app.run(debug=True, port=8001)