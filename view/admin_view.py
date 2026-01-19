from flask import Blueprint, session, redirect
import requests
from utils import wrap_layout, API_URL

admin_view_bp = Blueprint('admin_view', __name__)

@admin_view_bp.route("/admin/home")
def admin_home():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    stats = {
        "users": 0, "students": 0, "companies": 0,
        "jobs": 0, "open_jobs": 0, "closed_jobs": 0, "applications": 0
    }

    try:
        res = requests.get(f"{API_URL}/admin/home")
        if res.status_code == 200:
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
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    users = []
    try:
        users = requests.get(f"{API_URL}/admin/users").json()
    except:
        pass

    rows = ""
    for u in users:
        action = (
            f"<a href='/admin/users/{u['id']}/lock'>🔒 Lock</a>"
            if u["status"] == "active"
            else f"<a href='/admin/users/{u['id']}/unlock'>🔓 Unlock</a>"
        )

        rows += f"""
        <tr>
            <td>{u['id']}</td>
            <td>{u['email']}</td>
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

@admin_view_bp.route("/admin/users/<int:user_id>/lock")
def admin_lock_user(user_id):
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    requests.put(f"{API_URL}/admin/users/{user_id}/lock")
    return redirect("/admin/users")

@admin_view_bp.route("/admin/users/<int:user_id>/unlock")
def admin_unlock_user(user_id):
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    requests.put(f"{API_URL}/admin/users/{user_id}/unlock")
    return redirect("/admin/users")

@admin_view_bp.route("/admin/jobs")
def admin_jobs():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    jobs = []
    try:
        jobs = requests.get(f"{API_URL}/admin/jobs").json()
    except:
        pass

    rows = ""
    for j in jobs:
        action = ""
        if j["status"] != "CLOSED":
            action = f"<a href='/admin/jobs/{j['id']}/close'>❌ Close</a>"

        rows += f"""
        <tr>
            <td>{j['id']}</td>
            <td>{j['title']}</td>
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

@admin_view_bp.route("/admin/jobs/<int:job_id>/close")
def admin_close_job(job_id):
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    requests.put(f"{API_URL}/admin/jobs/{job_id}/close")
    return redirect("/admin/jobs")

@admin_view_bp.route("/admin/tests")
def admin_tests():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    tests = requests.get(f"{API_URL}/admin/tests").json()

    rows = ""
    for t in tests:
        rows += f"""
        <tr>
            <td>{t['id']}</td>
            <td>{t['testName']}</td>
            <td>{t['jobId']}</td>
            <td>
                <a href="/admin/tests/{t['id']}/delete">🗑 Delete</a>
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