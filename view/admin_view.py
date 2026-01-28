from flask import Blueprint, request, redirect, make_response
import requests
import secrets
from utils import wrap_layout, API_URL, get_current_user_from_jwt, auth_headers
from markupsafe import escape

admin_view_bp = Blueprint("admin_view", __name__)

def require_admin_view():
    user = get_current_user_from_jwt()
    if not user:
        return None
    if user.get("role") != "admin":
        return None
    return user

def generate_csrf_token():
    return secrets.token_hex(16)

def validate_csrf(form_token):
    cookie_token = request.cookies.get("csrf_token")
    return cookie_token and form_token and cookie_token == form_token


@admin_view_bp.route("/admin/home")
def admin_home():
    user = require_admin_view()
    if not user:
        return redirect("/login")

    stats = {
        "users": 0, "students": 0, "companies": 0,
        "jobs": 0, "open_jobs": 0, "closed_jobs": 0, "applications": 0
    }

    res = requests.get(
        f"{API_URL}/admin/home",
        headers=auth_headers(),
        timeout=5
    )
    if res.status_code == 200:
        data = res.json()
        stats["users"] = data["users"]["total"]
        stats["students"] = data["users"]["students"]
        stats["companies"] = data["users"]["companies"]
        stats["jobs"] = data["jobs"]["total"]
        stats["open_jobs"] = data["jobs"]["open"]
        stats["closed_jobs"] = data["jobs"]["closed"]
        stats["applications"] = data["applications"]

    content = f"""
    <h2>📊 Admin Dashboard</h2>

    <div class="job-card">
        👥 Users: <b>{stats['users']}</b><br>
        🎓 Students: <b>{stats['students']}</b><br>
        🏢 Companies: <b>{stats['companies']}</b>
    </div>

    <div class="job-card">
        📄 Jobs: <b>{stats['jobs']}</b><br>
        🟢 Open: <b>{stats['open_jobs']}</b><br>
        🔴 Closed: <b>{stats['closed_jobs']}</b>
    </div>

    <div class="job-card">
        📥 Applications: <b>{stats['applications']}</b>
    </div>
    """
    return wrap_layout(content)


@admin_view_bp.route("/admin/users")
def admin_users():
    user = require_admin_view()
    if not user:
        return redirect("/login")

    csrf_token = generate_csrf_token()

    res = requests.get(
        f"{API_URL}/admin/users",
        headers=auth_headers(),
        timeout=5
    )
    users = res.json() if res.status_code == 200 else []

    rows = ""
    for u in users:
        action = f"""
        <form method="post" action="/admin/users/{u['id']}/{'lock' if u['status']=='active' else 'unlock'}">
            <input type="hidden" name="csrf_token" value="{csrf_token}">
            <button>{'🔒 Lock' if u['status']=='active' else '🔓 Unlock'}</button>
        </form>
        """

        rows += f"""
        <tr>
            <td>{u['id']}</td>
            <td>{escape(u['email'])}</td>
            <td>{u['role']}</td>
            <td>{u['status']}</td>
            <td>{action}</td>
        </tr>
        """

    resp = make_response(wrap_layout(f"""
    <h2>👥 User Management</h2>
    <table border="1" width="100%" cellpadding="10">
        <tr>
            <th>ID</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th>
        </tr>
        {rows}
    </table>
    """))

    resp.set_cookie("csrf_token", csrf_token, httponly=True, samesite="Lax")
    return resp


@admin_view_bp.route("/admin/users/<int:user_id>/lock", methods=["POST"])
def admin_lock_user(user_id):
    if not validate_csrf(request.form.get("csrf_token")):
        return "CSRF invalid", 400

    if not require_admin_view():
        return redirect("/login")

    requests.put(
        f"{API_URL}/admin/users/{user_id}/lock",
        headers=auth_headers()
    )
    return redirect("/admin/users")


@admin_view_bp.route("/admin/users/<int:user_id>/unlock", methods=["POST"])
def admin_unlock_user(user_id):
    if not validate_csrf(request.form.get("csrf_token")):
        return "CSRF invalid", 400

    if not require_admin_view():
        return redirect("/login")

    requests.put(
        f"{API_URL}/admin/users/{user_id}/unlock",
        headers=auth_headers()
    )
    return redirect("/admin/users")


@admin_view_bp.route("/admin/jobs")
def admin_jobs():
    user = require_admin_view()
    if not user:
        return redirect("/login")

    csrf_token = generate_csrf_token()

    res = requests.get(
        f"{API_URL}/admin/jobs",
        headers=auth_headers(),
        timeout=5
    )
    jobs = res.json() if res.status_code == 200 else []

    rows = ""
    for j in jobs:
        action = ""
        if j["status"] != "CLOSED":
            action = f"""
            <form method="post" action="/admin/jobs/{j['id']}/close">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <button type="submit">❌ Close</button>
            </form>
            """

        rows += f"""
        <tr>
            <td>{j['id']}</td>
            <td>{escape(j['title'])}</td>
            <td>{j['companyId']}</td>
            <td>{j['status']}</td>
            <td>{action}</td>
        </tr>
        """

    resp = make_response(wrap_layout(f"""
    <h2>📄 Job Posting Management</h2>
    <table border="1" width="100%" cellpadding="10">
        <tr>
            <th>ID</th><th>Title</th><th>Company</th><th>Status</th><th>Action</th>
        </tr>
        {rows}
    </table>
    """))

    resp.set_cookie("csrf_token", csrf_token, httponly=True, samesite="Lax")
    return resp


@admin_view_bp.route("/admin/jobs/<int:job_id>/close", methods=["POST"])
def admin_close_job(job_id):
    if not validate_csrf(request.form.get("csrf_token")):
        return "CSRF token không hợp lệ", 400

    if not require_admin_view():
        return redirect("/login")

    requests.put(
        f"{API_URL}/admin/jobs/{job_id}/close",
        headers=auth_headers()
    )
    return redirect("/admin/jobs")


@admin_view_bp.route("/admin/tests")
def admin_tests():
    user = require_admin_view()
    if not user:
        return redirect("/login")

    csrf_token = generate_csrf_token()

    res = requests.get(
        f"{API_URL}/admin/tests",
        headers=auth_headers(),
        timeout=5
    )
    tests = res.json() if res.status_code == 200 else []

    rows = ""
    for t in tests:
        rows += f"""
        <tr>
            <td>{t['id']}</td>
            <td>{escape(t['testName'])}</td>
            <td>{t['jobId']}</td>
            <td>
                <form method="post" action="/admin/tests/{t['id']}/delete">
                    <input type="hidden" name="csrf_token" value="{csrf_token}">
                    <button type="submit">🗑 Delete</button>
                </form>
            </td>
        </tr>
        """

    resp = make_response(wrap_layout(f"""
    <h2>📝 Tests Management</h2>
    <table border="1" width="100%" cellpadding="10">
        <tr>
            <th>ID</th><th>Name</th><th>Job</th><th>Action</th>
        </tr>
        {rows}
    </table>
    """))

    resp.set_cookie("csrf_token", csrf_token, httponly=True, samesite="Lax")
    return resp

    
@admin_view_bp.route("/admin/tests/<int:test_id>/delete", methods=["POST"])
def admin_delete_test(test_id):
    if not validate_csrf(request.form.get("csrf_token")):
        return "CSRF token không hợp lệ", 400

    if not require_admin_view():
        return redirect("/login")

    requests.delete(
        f"{API_URL}/admin/tests/{test_id}",
        headers=auth_headers()
    )
    return redirect("/admin/tests")
