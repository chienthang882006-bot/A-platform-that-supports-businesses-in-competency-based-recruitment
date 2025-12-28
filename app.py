from flask import Flask, request, session, redirect, url_for
import requests

app = Flask(__name__)
app.secret_key = 'labodc_secret_key'
API_URL = "http://127.0.0.1:8000/api"


# ======================
# LAYOUT
# ======================
def wrap_layout(content):
    # Các trang KHÔNG hiển thị sidebar
    hide_sidebar = request.path in ['/auth', '/login', '/register']

    # ===== SIDEBAR =====
    if 'user' in session and not hide_sidebar:
        user = session['user']

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
            /* ===== RESET ===== */
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f0f2f5;
            }}

            /* ===== APP BAR ===== */
            .app-bar {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 60px;
                background: white;
                display: flex;
                align-items: center;
                padding: 0 20px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                z-index: 1000;
            }}

            .app-title {{
                font-size: 22px;
                font-weight: bold;
                color: #0f172a;
                text-decoration: none;
            }}

            /* ===== SIDEBAR ===== */
            .sidebar {{
                position: fixed;
                top: 60px;
                left: 0;
                width: 220px;
                height: calc(100vh - 60px);
                background: #0f172a;
                color: white;
                padding: 20px 15px;
                box-sizing: border-box;
            }}

            .profile {{
                text-align: center;
                margin-bottom: 30px;
            }}

            .avatar {{
                width: 72px;
                height: 72px;
                border-radius: 50%;
                object-fit: cover;
                border: 2px solid white;
                margin-bottom: 10px;
            }}

            .email {{
                font-size: 13px;
                word-break: break-all;
            }}

            .role {{
                font-size: 12px;
                color: #94a3b8;
                margin-top: 4px;
            }}

            .menu a {{
                display: block;
                padding: 10px 12px;
                margin-bottom: 6px;
                border-radius: 8px;
                text-decoration: none;
                color: #e5e7eb;
                font-size: 14px;
            }}

            .menu a:hover {{
                background: #1e293b;
            }}

            /* ===== MAIN CONTENT ===== */
            .main {{
                margin-left: 220px;
                margin-top: 60px;
                padding: 30px;
                min-height: calc(100vh - 60px);
                background: white;
                box-sizing: border-box;
            }}

            /* ===== NO SIDEBAR (AUTH) ===== */
            .no-sidebar .main {{
                margin-left: 0;
            }}

            /* ===== COMMON UI ===== */
            .job-card {{
                border-left: 6px solid #ff4b4b;
                padding: 15px;
                margin: 15px 0;
                background: #fafafa;
                border-radius: 8px;
            }}

            label {{
                font-weight: bold;
                margin-top: 12px;
                display: block;
            }}

            input, select, textarea {{
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                border-radius: 5px;
                border: 1px solid #ddd;
            }}

            textarea {{
                resize: vertical;
                min-height: 90px;
            }}

            button {{
                background: #2563eb;
                color: white;
                padding: 10px;
                border: none;
                width: 100%;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            }}

            button:hover {{
                background: #1e40af;
            }}
        </style>
    </head>

    <body class="{ 'no-sidebar' if hide_sidebar else '' }">

        <!-- APP BAR -->
        <div class="app-bar">
            <a href="/student/home" class="app-title">🚀 LabOdc Recruitment</a>
        </div>

        <!-- SIDEBAR -->
        {sidebar}

        <!-- MAIN -->
        <div class="main">
            {content}
        </div>

    </body>
    </html>
    """





# ======================
# NOTIFICATIONS
# ======================
def show_notifications():
    if 'user' in session:
        try:
            res = requests.get(f"{API_URL}/notifications/{session['user']['id']}")
            if res.status_code == 200:
                notifs = res.json()
                html = "<h4>🔔 Thông báo mới</h4>"
                for n in notifs[:3]:
                    html += f"<p>- {n['content']}</p>"
                return html
        except:
            pass
    return ""


# ======================
# HOME / JOB LIST
# ======================
@app.route('/')
def index():
    return redirect('/auth')


# ======================
# REGISTER / LOGIN
# ======================
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

                # 🎯 Điều hướng theo role
                if user['role'] == 'student':
                    return redirect('/student/home')
                elif user['role'] == 'company':
                    return redirect('/company/home')
                elif user['role'] == 'admin':
                    return redirect('/admin/dashboard')

                # fallback
                return redirect('/login')

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


@app.route("/student/home")
def student_home():
    if "user" not in session or session["user"]["role"] != "student":
        return redirect("/login")

    try:
        # lấy danh sách job
        res = requests.get(f"{API_URL}/jobs/")
        jobs = res.json() if res.status_code == 200 else []
    except:
        jobs = []

    content = "<h2>💼 Danh sách việc làm</h2>"

    for j in jobs:
        content += f"""
        <div class="job-card">
            <h3>{j['title']}</h3>
            <p>{j['description']}</p>

            <!-- Ứng tuyển -->
            <form method="post" action="/apply/{j['id']}">
                <button>✅ Ứng tuyển</button>
            </form>

            <!-- Làm bài test -->
            <form method="get" action="/student/tests/{j['id']}">
                <button>📝 Làm bài test</button>
            </form>
        </div>
        """

    return wrap_layout(content)



# ======================
# APPLY JOB
# ======================
@app.route("/apply/<int:job_id>", methods=["POST"])
def apply(job_id):
    user_id = session["user"]["id"]

    # gọi backend lấy student theo user_id
    res_student = requests.get(f"{API_URL}/students/user/{user_id}")
    student = res_student.json()

    student_id = student["id"]

    res = requests.post(
        f"{API_URL}/apply/",
        json={
            "studentId": student_id,
            "jobId": job_id
        }
    )

    if res.status_code == 200 or res.status_code == 201:
        return redirect("/student/home")

    return "Ứng tuyển thất bại", 400


# ======================
# STUDENT PROFILE
# ======================
@app.route("/student/profile", methods=["GET", "POST"])
def student_profile():
    if 'user' not in session:
        return redirect('/login')

    user_id = session['user']['id']

    try:
        # 1️⃣ Lấy student theo user
        stu_res = requests.get(f"{API_URL}/students/user/{user_id}")
        if stu_res.status_code != 200:
            return wrap_layout("<p>⚠️ Chưa có hồ sơ sinh viên</p>")

        student = stu_res.json()
        student_id = student['id']

        message = ""

        # 2️⃣ Nếu submit form → update profile
        if request.method == "POST":
            payload = {
                "fullName": request.form.get("fullName"),
                "major": request.form.get("major"),
                "about": request.form.get("about"),
                "educationLevel": request.form.get("educationLevel"),
                "degrees": request.form.get("degrees"),
                "cvUrl": request.form.get("cvUrl")
            }

            res = requests.put(
                f"{API_URL}/students/{student_id}",
                json=payload
            )

            if res.status_code == 200:
                message = "<p style='color:green;'>✅ Cập nhật hồ sơ thành công</p>"
                # reload lại data
                student = requests.get(f"{API_URL}/students/user/{user_id}").json()
            else:
                message = "<p style='color:red;'>❌ Cập nhật thất bại</p>"

        profile = student.get("profile") or {}

        # 3️⃣ Render form
        content = f"""
        <h2>👤 Hồ sơ sinh viên</h2>
        {message}
        <form method="post">
            <label>Họ tên</label>
            <input name="fullName" value="{student.get('fullName','')}" required>

            <label>Ngành học</label>
            <input name="major" value="{student.get('major','')}">

            <label>Giới thiệu</label>
            <textarea name="about" rows="4">{profile.get('about','')}</textarea>

            <label>Trình độ học vấn</label>
            <input name="educationLevel" value="{profile.get('educationLevel','')}">

            <label>Bằng cấp</label>
            <input name="degrees" value="{profile.get('degrees','')}">

            <label>Link CV</label>
            <input name="cvUrl" value="{profile.get('cvUrl','')}">

            <button style="margin-top:15px;">💾 Lưu hồ sơ</button>
        </form>

        """

        return wrap_layout(content)

    except Exception as e:
        return wrap_layout(f"<p>❌ Lỗi tải hồ sơ: {e}</p>")

# ======================
# STUDENT APPLICATIONS
# ======================
@app.route('/student/applications')
def student_applications():
    if 'user' not in session:
        return redirect('/login')

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
@app.route('/auth')
def auth():
    return wrap_layout("""
    <h2>🔐 Xác thực người dùng</h2>
    <p>Vui lòng chọn chức năng:</p>

    <div style="display:flex; gap:20px; margin-top:20px;">
        <a href="/login" style="
            flex:1;
            text-align:center;
            padding:15px;
            background:#2563eb;
            color:white;
            border-radius:8px;
            text-decoration:none;
            font-weight:bold;
        ">
            🔑 Đăng nhập
        </a>

        <a href="/register" style="
            flex:1;
            text-align:center;
            padding:15px;
            background:#16a34a;
            color:white;
            border-radius:8px;
            text-decoration:none;
            font-weight:bold;
        ">
            📝 Đăng ký
        </a>
    </div>
    """)


@app.route("/student/tests/<int:job_id>")
def student_tests(job_id):
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect('/login')

    try:
        res = requests.get(f"{API_URL}/jobs/{job_id}/tests")
        tests = res.json() if res.status_code == 200 else []
    except:
        tests = []

    content = "<h2>📝 Bài test cho công việc</h2>"

    if not tests:
        content += "<p>⚠️ Chưa có bài test cho job này</p>"

    for t in tests:
        content += f"""
        <div class="job-card">
            <b>{t['testName']}</b><br>
            Thời gian: {t['duration']} phút<br>
            Tổng điểm: {t['totalScore']}
            <form method="post" action="/student/tests/{t['id']}/submit">
                <label>Nhập điểm (demo)</label>
                <input type="number" name="score" required>
                <button>📤 Nộp bài</button>
            </form>
        </div>
        """

    return wrap_layout(content)


@app.route("/student/tests/<int:test_id>/submit", methods=["POST"])
def submit_test(test_id):
    if 'user' not in session:
        return redirect('/login')

    user_id = session['user']['id']

    # Lấy student theo user
    res_student = requests.get(f"{API_URL}/students/user/{user_id}")
    student = res_student.json()
    student_id = student["id"]

    score = request.form["score"]

    res = requests.post(
        f"{API_URL}/tests/{test_id}/submit",
        json={
            "studentId": student_id,
            "score": int(score)
        }
    )

    if res.status_code in [200, 201]:
        return redirect("/student/home")

    return "❌ Nộp bài test thất bại", 400

# ======================
# COMPANY
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

    content = """
    <h2>📄 Tin tuyển dụng của công ty</h2>

    <a href="/company/jobs/create" style="
        display:inline-block;
        margin:10px 0;
        padding:10px 14px;
        background:#16a34a;
        color:white;
        border-radius:6px;
        text-decoration:none;
        font-weight:bold;
    ">
        ➕ Tạo Job mới
    </a>
    """

    try:
        # 👉 LẤY DANH SÁCH JOB
        jobs = requests.get(f"{API_URL}/jobs/").json()
    except:
        jobs = []

    # 👉 HIỂN THỊ TỪNG JOB + LINK THÊM TEST
    for j in jobs:
        content += f"""
        <div class="job-card">
            <h3>{j['title']}</h3>
            <p>{j['description']}</p>

            <a href="/company/jobs/{j['id']}/test" style="
                display:inline-block;
                margin-right:10px;
                color:#2563eb;
                font-weight:bold;
                text-decoration:none;
            ">
                📝 Thêm bài test
            </a>

            <a href="/company/jobs/{j['id']}/applications" style="
                color:#16a34a;
                font-weight:bold;
                text-decoration:none;
            ">
                📥 Xem ứng viên
            </a>
        </div>
        """

    return wrap_layout(content)




@app.route('/company/applications')
def company_applications():
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')

    content = "<h2>📥 Danh sách ứng viên</h2>"
    content += "<p>(Sẽ triển khai tiếp)</p>"
    return wrap_layout(content)


@app.route('/company/jobs/create', methods=['GET', 'POST'])
def company_create_job():
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')

    message = ""

    if request.method == 'POST':
        try:
            # Lấy company theo user
            company = requests.get(
                f"{API_URL}/companies/user/{session['user']['id']}"
            ).json()

            payload = {
                "companyId": company['id'],
                "title": request.form['title'],
                "description": request.form['description'],
                "location": request.form['location'],
                "status": "open"
            }

            res = requests.post(f"{API_URL}/jobs/", json=payload)

            if res.status_code in [200, 201]:
                message = "✅ Tạo job thành công"
            else:
                message = "❌ Tạo job thất bại"
        except:
            message = "❌ Lỗi backend"

    return wrap_layout(f"""
    <h2>📄 Tạo tin tuyển dụng</h2>
    <p>{message}</p>

    <form method="post">
        <label>Tiêu đề</label>
        <input name="title" required>

        <label>Mô tả</label>
        <textarea name="description" required></textarea>

        <label>Địa điểm</label>
        <input name="location">

        <button>➕ Tạo Job</button>
    </form>
    """)


@app.route('/company/jobs/<int:job_id>/test', methods=['GET', 'POST'])
def company_create_test(job_id):
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')

    message = ""

    if request.method == 'POST':
        payload = {
            "testName": request.form['testName'],
            "duration": int(request.form['duration']),
            "totalScore": int(request.form['totalScore'])
        }

        res = requests.post(
            f"{API_URL}/jobs/{job_id}/test",
            json=payload
        )

        if res.status_code in [200, 201]:
            message = "✅ Tạo bài test thành công"
        else:
            message = "❌ Tạo bài test thất bại"

    return wrap_layout(f"""
    <h2>📝 Tạo bài Test cho Job #{job_id}</h2>
    <p>{message}</p>

    <form method="post">
        <label>Tên bài test</label>
        <input name="testName" required>

        <label>Thời gian (phút)</label>
        <input type="number" name="duration" required>

        <label>Tổng điểm</label>
        <input type="number" name="totalScore" required>

        <button>➕ Tạo Test</button>
    </form>
    """)


@app.route('/company/jobs/<int:job_id>/applications')
def company_view_applicants(job_id):
    if 'user' not in session or session['user']['role'] != 'company':
        return redirect('/login')

    try:
        apps = requests.get(
            f"{API_URL}/jobs/{job_id}/applications"
        ).json()
    except:
        apps = []

    content = f"<h2>📥 Ứng viên cho Job #{job_id}</h2>"

    for a in apps:
        content += f"""
        <div class="job-card">
            <b>{a['studentName']}</b><br>
            Trạng thái: {a['status']}<br>
            <a href="{a['cvUrl']}" target="_blank">📄 Xem CV</a>
        </div>
        """

    return wrap_layout(content)

# ======================
# RUN APP (CHỈ 1 LẦN)
# ======================
if __name__ == '__main__':
    app.run(debug=True, port=8001)
