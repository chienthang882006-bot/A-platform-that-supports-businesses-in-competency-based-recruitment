from flask import Blueprint, session, redirect
import requests
from utils import wrap_layout, API_URL
from markupsafe import escape

admin_view_bp = Blueprint('admin_view', __name__)

def require_admin_view():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')
    return None

def safe_api_request(method, url):
    try:
        return requests.request(method, url, timeout=3)
    except requests.RequestException:
        return None

@admin_view_bp.route("/admin/home")
def admin_home():
    auth = require_admin_view()
    if auth: return auth

    stats = {
        "users": 0, "students": 0, "companies": 0,
        "jobs": 0, "open_jobs": 0, "closed_jobs": 0, "applications": 0
    }

    try:
        res = safe_api_request("GET", f"{API_URL}/admin/home")
        if res and res.status_code == 200:
            data = res.json()

            stats["users"] = data["users"]["total"]
            stats["students"] = data["users"]["students"]
            stats["companies"] = data["users"]["companies"]
            stats["jobs"] = data["jobs"]["total"]
            stats["open_jobs"] = data["jobs"]["open"]
            stats["closed_jobs"] = data["jobs"]["closed"]
            stats["applications"] = data["applications"]
    except Exception as e:
        print("Admin dashboard error:", e)

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
    auth = require_admin_view()
    if auth: return auth

    users = []
    try:
        res = safe_api_request("GET", f"{API_URL}/admin/users")
        users = res.json() if res and res.status_code == 200 else []
    except:
        pass

    rows = ""
    for u in users:
        if u["status"] == "active":
            action = f"""
            <form method="post" action="/admin/users/{u['id']}/lock" style="display:inline">
                <button type="submit">🔒 Lock</button>
            </form>
            """
        else:
            action = f"""
            <form method="post" action="/admin/users/{u['id']}/unlock" style="display:inline">
                <button type="submit">🔓 Unlock</button>
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

    content = f"""
    <h2>👥 User Management</h2>
    <table border="1" width="100%" cellpadding="10">
        <tr>
            <th>ID</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th>
        </tr>
        {rows}
    </table>
    """
    return wrap_layout(content)

@admin_view_bp.route("/admin/users/<int:user_id>/lock", methods=["POST"])
def admin_lock_user(user_id):
    auth = require_admin_view()
    if auth: return auth

    safe_api_request("PUT", f"{API_URL}/admin/users/{user_id}/lock")
    return redirect("/admin/users")

@admin_view_bp.route("/admin/users/<int:user_id>/unlock", methods=["POST"])
def admin_unlock_user(user_id):
    auth = require_admin_view()
    if auth: return auth

    safe_api_request("PUT", f"{API_URL}/admin/users/{user_id}/unlock")
    return redirect("/admin/users")

@admin_view_bp.route("/admin/jobs")
def admin_jobs():
    auth = require_admin_view()
    if auth: return auth

    jobs = []
    try:
        res = safe_api_request("GET", f"{API_URL}/admin/jobs")
        jobs = res.json() if res and res.status_code == 200 else []
    except:
        pass

    rows = ""
    for j in jobs:
        action = ""
        if j["status"] != "CLOSED":
            action = f"""
            <form method="post" action="/admin/jobs/{j['id']}/close" style="display:inline">
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

    content = f"""
    <h2>📄 Job Posting Management</h2>
    <table border="1" width="100%" cellpadding="10">
        <tr>
            <th>ID</th><th>Title</th><th>Company</th><th>Status</th><th>Action</th>
        </tr>
        {rows}
    </table>
    """
    return wrap_layout(content)

@admin_view_bp.route("/admin/jobs/<int:job_id>/close", methods=["POST"])
def admin_close_job(job_id):
    auth = require_admin_view()
    if auth: return auth

    safe_api_request("PUT", f"{API_URL}/admin/jobs/{job_id}/close")
    return redirect("/admin/jobs")

@admin_view_bp.route("/admin/tests")
def admin_tests():
    auth = require_admin_view()
    if auth: return auth

    res = safe_api_request("GET", f"{API_URL}/admin/tests")
    tests = res.json() if res and res.status_code == 200 else []

    rows = ""
    for t in tests:
        rows += f"""
        <tr>
            <td>{t['id']}</td>
            <td>{escape(t['testName'])}</td>
            <td>{t['jobId']}</td>
            <td>
                <form method="post" action="/admin/tests/{t['id']}/delete" style="display:inline">
                    <button type="submit">🗑 Delete</button>
                </form>
            </td>
        </tr>
        """

    return wrap_layout(f"""
    <h2>📝 Tests Management</h2>
    <table border="1" width="100%" cellpadding="10">
        <tr>
            <th>ID</th><th>Name</th><th>Job</th><th>Action</th>
        </tr>
        {rows}
    </table>
    """)
    
@admin_view_bp.route("/admin/tests/<int:test_id>/delete", methods=["POST"])
def admin_delete_test(test_id):
    auth = require_admin_view()
    if auth: return auth

    safe_api_request("DELETE", f"{API_URL}/admin/tests/{test_id}")
    return redirect("/admin/tests")
