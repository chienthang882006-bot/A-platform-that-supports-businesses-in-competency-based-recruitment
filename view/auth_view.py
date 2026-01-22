from flask import Blueprint, request, redirect, make_response
from flask_wtf.csrf import generate_csrf
from markupsafe import escape
import requests
import re
from utils import wrap_layout, API_URL

auth_bp = Blueprint('auth_view', __name__)

def is_strong_password(password: str) -> bool:
    if len(password) < 6:
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
    
    csrf_token = generate_csrf()
    
    message = ""

    if request.method == 'POST':
        role = request.form.get("role")
        if role not in ["student", "company"]:
            role = "student"

        email = request.form.get("email", "").strip()[:100]
        password = request.form.get("password", "")[:128]

        if "@" not in email or "." not in email:
            message = "Email không hợp lệ, Vui lòng thử lại"

        elif not is_strong_password(password):
            message = (
                "Mật khẩu phải từ 6 ký tự, gồm chữ hoa, chữ thường, số "
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
                message = "Không kết nối được backend"

    return wrap_layout(f"""
    <h2>📝 Đăng ký</h2>
    <p>{escape(message)}</p>
    <form method="post">
        <input type="hidden" name="csrf_token" value="{ csrf_token }">
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

    csrf_token = generate_csrf()
    
    message = ""

    if request.method == 'POST':
        email = request.form.get("email", "").strip().lower()[:100]
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
                    try:
                        data = res.json()
                        token = data.get("access_token")
                        user = data.get("user", {})
                        role = user.get("role")
                        
                        if role not in ("student", "company", "admin"):
                            return redirect("/auth")

                        if not token or not role:
                            message = "Lỗi dữ liệu đăng nhập"
                        else:
                            resp = make_response(
                                redirect(f"/{role}/home")
                            )
                            resp.set_cookie(
                                "ui_access_token",
                                token,
                                httponly=True,
                                samesite="Lax",
                                secure=request.is_secure,
                                max_age=3600
                            )
                            return resp

                    except Exception as e:
                        message = f"Lỗi xử lý login: {e}"

                else:
                    try:
                        message = res.json().get(
                            "detail", "Sai tài khoản hoặc mật khẩu"
                        )
                    except Exception:
                        message = "Sai tài khoản hoặc mật khẩu"

            except requests.exceptions.RequestException as e:
                message = f"Lỗi backend: {e}"

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


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    resp = make_response(redirect('/auth'), 302)
    resp.delete_cookie("ui_access_token")
    resp.delete_cookie("csrf_token")
    return resp

