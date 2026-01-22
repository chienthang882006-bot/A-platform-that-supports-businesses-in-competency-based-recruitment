# utils.py
from flask import request
import jwt
import os
import requests


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

def get_current_user_from_jwt():
    # 1. Ưu tiên header (API call)
    auth = request.headers.get("Authorization")

    # 2. Nếu không có → lấy từ cookie UI
    if not auth:
        token = request.cookies.get("ui_access_token")
        if not token:
            return None
        auth = f"Bearer {token}"

    try:
        payload = jwt.decode(
            auth.replace("Bearer ", ""),
            JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_sub": False}
        )
        return {
            "id": int(payload.get("sub")),
            "role": payload.get("role")
        }
    except jwt.InvalidTokenError:
        return None


def auth_headers():
    token = request.cookies.get("ui_access_token")
    if not token:
        return {}
    return {
        "Authorization": f"Bearer {token}"
    }


# CẤU HÌNH API URL
API_URL = "http://127.0.0.1:8001/api"

def show_notifications():
    user = get_current_user_from_jwt()
    if not user:
        return ""
    
    try:
        res = requests.get(
            f"{API_URL}/notifications/{user['id']}",
            headers=auth_headers(),
            timeout=5
        )
        count = 0
        list_html = ""

        if res.status_code == 200:
            notifs = res.json()
            count = len(notifs)
            if count == 0:
                list_html = "<div class='notif-item'>Không có thông báo mới</div>"
            else:
                for n in notifs[:5]:
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
    
    user = get_current_user_from_jwt()
    
    notif_html = show_notifications()
    
    if user and not hide_sidebar:
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
        elif user['role'] == 'admin':
            menu = """
            <a href="/admin/home">🏠 Admin Home</a>
            <a href="/admin/users">👥 Quản lý Users</a>
            <a href="/admin/jobs">📄 Duyệt Job</a>
            """

        sidebar = f"""
        <div class="sidebar">
            <div class="profile">
                <div class="email">User</div>
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

    # CSS Styles (Giữ nguyên như cũ)
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>LabOdc Recruitment</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            /* ===== BASIC STYLES ===== */
            body {{ margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; color: #333; }}
            
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
                min-height: calc(100vh - 60px); background: #f8fafc; box-sizing: border-box;
            }}
            .no-sidebar .main {{ margin-left: 0; }}

            /* UI ELEMENTS */
            .job-card {{
                border-left: 5px solid #2563eb; padding: 20px; margin: 15px 0;
                background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            label {{ font-weight: 600; margin-top: 12px; display: block; font-size: 14px; color: #334155; }}
            input, select, textarea {{
                width: 100%; padding: 10px; margin: 8px 0;
                border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;
                box-sizing: border-box;
            }}
            input:focus, select:focus, textarea:focus {{ outline: 2px solid #2563eb; border-color: transparent; }}
            
            button {{
                background: #2563eb; color: white; padding: 10px; border: none;
                width: 100%; border-radius: 6px; cursor: pointer; font-weight: 600;
                transition: background 0.2s;
            }}
            button:hover {{ background: #1d4ed8; }}

            /* CV DETAILS STYLES */
            .cv-container {{ display: flex; gap: 20px; }}
            .cv-left {{ flex: 1; text-align: center; padding-right: 20px; border-right: 1px solid #e2e8f0; }}
            .cv-right {{ flex: 2; }}
            .badge-skill {{ 
                display: inline-block; background: #e0f2fe; color: #0284c7; 
                padding: 5px 10px; border-radius: 20px; font-size: 12px; 
                margin-right: 5px; margin-bottom: 5px; font-weight: 600;
            }}
            .section-title {{ 
                font-size: 16px; font-weight: bold; color: #2563eb; 
                border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; margin-top: 20px; margin-bottom: 10px; 
            }}
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