from flask import Blueprint, request, session, redirect
import requests
from utils import wrap_layout, API_URL

auth_bp = Blueprint('auth_view', __name__)

@auth_bp.route('/')
def index():
    return redirect('/auth')

@auth_bp.route('/auth')
def auth():
    return wrap_layout("""
    <h2>🔐 Xác thực người dùng</h2>
    <p>Vui lòng chọn chức năng:</p>
    <div style="display:flex; gap:20px; margin-top:20px;">
        <a href="/login" style="flex:1; text-align:center; padding:15px; background:#2563eb; color:white; border-radius:8px; text-decoration:none; font-weight:bold;">🔑 Đăng nhập</a>
        <a href="/register" style="flex:1; text-align:center; padding:15px; background:#16a34a; color:white; border-radius:8px; text-decoration:none; font-weight:bold;">📝 Đăng ký</a>
    </div>
    """)

@auth_bp.route('/register', methods=['GET', 'POST'])
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

@auth_bp.route('/login', methods=['GET', 'POST'])
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
                elif user['role'] == 'admin': return redirect('/admin/home')
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

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/auth')