from flask import Blueprint, request, session, redirect
from markupsafe import escape
import requests
import secrets
import re
from utils import wrap_layout, API_URL
from datetime import datetime, timedelta

auth_bp = Blueprint('auth_view', __name__)

def get_client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(16)
    return session["_csrf_token"]


def validate_csrf(token):
    return token and session.get("_csrf_token") == token

MAX_LOGIN_ATTEMPTS = 5
LOCK_TIME_MINUTES = 5

def is_login_locked():
    locked_until = session.get("login_locked_until")
    if not locked_until:
        return False
    return datetime.utcnow() < locked_until

def register_failed_login():
    ip = get_client_ip()
    key = f"login_fail_{ip}"

    count = session.get(key, 0) + 1
    session[key] = count

    if count >= MAX_LOGIN_ATTEMPTS:
        session["login_locked_until"] = datetime.utcnow() + timedelta(minutes=LOCK_TIME_MINUTES)

def reset_login_attempts():
    ip = get_client_ip()
    session.pop(f"login_fail_{ip}", None)
    session.pop("login_locked_until", None)

def is_strong_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*()_+=\-]", password):
        return False
    return True
    

@auth_bp.route('/')
def index():
    return redirect('/auth')

@auth_bp.route('/auth')
def auth():
    return wrap_layout("""
    <h2>🔐 Xác thực người dùng</h2>
    <p>Vui lòng chọn chức năng:</p>
    <div style="display:flex; gap:20px; margin-top:20px;">
        <a href="/login" style="flex:1; text-align:center; padding:15px; background:#2563eb; color:white; border-radius:8px;">🔑 Đăng nhập</a>
        <a href="/register" style="flex:1; text-align:center; padding:15px; background:#16a34a; color:white; border-radius:8px;">📝 Đăng ký</a>
    </div>
    """)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    message = ""

    session.pop("_csrf_token", None)
    csrf_token = generate_csrf_token()

    if request.method == 'POST':
        if not validate_csrf(request.form.get("csrf_token")):
            return "CSRF token không hợp lệ", 400

        session.pop("_csrf_token", None)

        role = request.form.get("role")
        if role not in ["student", "company"]:
            role = "student"

        email = request.form.get("email", "").strip()[:100]
        password = request.form.get("password", "")[:128]

        if "@" not in email or "." not in email:
            message = "Email không hợp lệ, Vui lòng thử lại"

        elif not is_strong_password(password):
            message = (
                "Mật khẩu phải từ 8 ký tự, gồm chữ hoa, chữ thường, số "
                "và ký tự đặc biệt"
            )

        else:
            try:
                res = requests.post(
                    f"{API_URL}/users/",
                    json={
                        "email": email,
                        "password": password,
                        "role": role
                    },
                    timeout=5
                )

                if res.status_code in (200, 201):
                    message = "✅ Đăng ký thành công"
                else:
                    message = res.json().get("detail", "Lỗi đăng ký")

            except requests.exceptions.RequestException:
                message = "❌ Không kết nối được backend"

    return wrap_layout(f"""
    <h2>📝 Đăng ký</h2>
    <p>{escape(message)}</p>
    <form method="post">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        <input name="email" placeholder="Email" required>
        <input name="password" type="password" placeholder="Mật khẩu" required>
        <select name="role">
            <option value="student">Sinh viên</option>
            <option value="company">Doanh nghiệp</option>
        </select>
        <button>Đăng ký</button>
    </form>
    """)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    session.pop("_csrf_token", None)
    csrf_token = generate_csrf_token()

    if request.method == 'POST':

        if not validate_csrf(request.form.get("csrf_token")):
            return "CSRF token không hợp lệ", 400

        session.pop("_csrf_token", None)

        if is_login_locked():
            message = "Quá nhiều lần đăng nhập sai. Vui lòng thử lại sau 5 phút."
        else:
            email = request.form.get("email", "")[:100]
            password = request.form.get("password", "")[:128]

            if not email or not password:
                message = "Vui lòng nhập đầy đủ thông tin"
            else:
                try:
                    res = requests.post(
                        f"{API_URL}/login/",
                        json={"email": email, "password": password},
                        timeout=5
                    )

                    if res.status_code == 200:
                        user = res.json()

                        reset_login_attempts()
                        session.clear()
                        session.modified = True

                        session["user"] = {
                            "id": user["id"],
                            "email": user["email"],
                            "role": user["role"]
                        }

                        if user["role"] == "student":
                            return redirect("/student/home")
                        elif user["role"] == "company":
                            return redirect("/company/home")
                        elif user["role"] == "admin":
                            return redirect("/admin/home")

                    else:
                        register_failed_login()
                        message = "Sai tài khoản hoặc mật khẩu"

                except requests.exceptions.RequestException:
                    message = "Không kết nối được backend"

    return wrap_layout(f"""
    <h2>🔑 Đăng nhập</h2>
    <p>{escape(message)}</p>
    <form method="post">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        <input name="email" placeholder="Email" required>
        <input name="password" type="password" placeholder="Mật khẩu" required>
        <button>Đăng nhập</button>
    </form>
    """)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    session.modified = True
    return redirect('/auth')
