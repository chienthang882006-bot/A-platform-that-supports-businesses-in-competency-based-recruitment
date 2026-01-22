from flask import Blueprint, request, redirect, make_response
from markupsafe import escape
import requests
import json
import secrets
import jwt
from utils import wrap_layout, API_URL, get_current_user_from_jwt, auth_headers


company_view_bp = Blueprint('company_view', __name__)

def require_company_view():
    user = get_current_user_from_jwt()
    if not user:
        return None
    if user["role"] != "company":
        return None
    return user


def validate_csrf(form_token):
    cookie_token = request.cookies.get("csrf_token")
    return cookie_token and form_token and cookie_token == form_token

def check_application_owner(app_id):
    user = require_company_view()
    if not user:
        return False

    user_id = user["id"]

    comp_res = requests.get(f"{API_URL}/companies/user/{user_id}",headers=auth_headers())
    if comp_res.status_code != 200:
        return False

    company_id = comp_res.json()["id"]
    check = requests.get(
        f"{API_URL}/companies/{company_id}/applications/{app_id}",
        headers=auth_headers()
    )
    return check.status_code == 200


@company_view_bp.route('/company/home')
def company_home():
    user = require_company_view()
    if not user:
        return redirect('/login')

    content = f"""
    <h2>🏢 Dashboard Doanh nghiệp</h2>
    <p>Xin chào <b>Doanh nghiệp</b></p>

    
    <div style="display:flex; gap:15px; flex-wrap:wrap;">
        <div class="job-card" style="flex:1; min-width:300px; border-left:5px solid #16a34a;">
            <h3>⚙️ Hồ sơ công ty</h3>
            <p>Cập nhật thông tin, logo, website để thu hút ứng viên.</p>
            <a href="/company/profile"><button style="background:#16a34a;">Cập nhật ngay</button></a>
        </div>

        <div class="job-card" style="flex:1; min-width:300px;">
            <h3>📄 Quản lý tin tuyển dụng</h3>
            <p>Xem, tạo mới và chỉnh sửa các bài đăng.</p>
            <a href="/company/jobs"><button>Xem danh sách</button></a>
        </div>

        <div class="job-card" style="flex:1; min-width:300px;">
            <h3>📥 Hồ sơ ứng tuyển</h3>
            <p>Xem danh sách ứng viên đã nộp hồ sơ.</p>
            <a href="/company/applications"><button>Xem ứng viên</button></a>
        </div>
    </div>
    """
    resp = make_response(wrap_layout(content))
    return resp


@company_view_bp.route('/company/profile', methods=['GET', 'POST'])
def company_profile():
    
    if request.method == "GET":
        csrf_token = secrets.token_hex(16)
    else:
        csrf_token = request.cookies.get("csrf_token")

    if request.method == 'POST':
        if not validate_csrf(request.form.get("csrf_token")):
            return wrap_layout("<h3>CSRF token không hợp lệ</h3>")

    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]   
    
    message = ""

    if request.method == 'POST':
        payload = {
            "companyName": request.form.get("companyName"),
            "website": request.form.get("website"),
            "address": request.form.get("address"),
            "industry": request.form.get("industry"),
            "size": request.form.get("size"),
            "logoUrl": request.form.get("logoUrl"),
            "description": request.form.get("description")
        }
        try:
            comp_res = requests.get(f"{API_URL}/companies/user/{user_id}", headers=auth_headers())
            if comp_res.status_code == 200:
                company_id = comp_res.json()['id']
                update_res = requests.put(f"{API_URL}/companies/{company_id}/profile", json=payload, headers=auth_headers())

                if update_res.status_code == 200:
                    message = "<div style='background:#dcfce7; color:#166534; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #bbf7d0; font-weight:bold;'>✅ Đã lưu hồ sơ thành công!</div>"
                else:
                    message = f"<div style='color:red; margin-bottom:15px;'>Lỗi API: {update_res.text}</div>"
        except Exception as e:
            message = f"<div style='color:red; margin-bottom:15px;'>Lỗi kết nối: {e}</div>"

    company = {}
    try:
        res = requests.get(f"{API_URL}/companies/user/{user_id}/profile", headers=auth_headers())
        if res.status_code == 200:
            company = res.json()
    except:
        pass

    content = f"""
    <h2>⚙️ Hồ sơ doanh nghiệp</h2>
    {message}
    
    <div class="job-card">
        <form method="post">
            <input type="hidden" name="csrf_token" value="{csrf_token}">
            <div style="display:flex; gap:30px;">
                <div style="flex:1; text-align:center;">
                    <div style="border: 2px dashed #cbd5e1; border-radius: 12px; padding: 10px; margin-bottom: 15px;">
                        <img src="{company.get('logoUrl') or 'https://via.placeholder.com/150?text=No+Logo'}" 
                             style="width:100%; height:150px; object-fit:contain; border-radius:8px;"
                             onerror="this.src='https://via.placeholder.com/150?text=Error'">
                    </div>
                    <label style="text-align:left; font-size:13px;">Link Logo (URL ảnh)</label>
                    <input name="logoUrl" value="{company.get('logoUrl', '')}" placeholder="https://example.com/logo.png">
                </div>

                <div style="flex:3;">
                    <label>Tên công ty <span style="color:red">*</span></label>
                    <input name="companyName" value="{company.get('companyName', '')}" required style="font-weight:bold;">
                    
                    <div style="display:flex; gap:15px;">
                        <div style="flex:1;">
                            <label>Website</label>
                            <input name="website" value="{company.get('website', '')}" placeholder="https://mycompany.com">
                        </div>
                        <div style="flex:1;">
                            <label>Quy mô nhân sự</label>
                            <select name="size">
                                <option value="">-- Chọn quy mô --</option>
                                <option value="Startup (1-10)" {'selected' if company.get('size')=='Startup (1-10)' else ''}>Startup (1-10)</option>
                                <option value="Vừa (10-50)" {'selected' if company.get('size')=='Vừa (10-50)' else ''}>Vừa (10-50)</option>
                                <option value="Lớn (50-200)" {'selected' if company.get('size')=='Lớn (50-200)' else ''}>Lớn (50-200)</option>
                                <option value="Tập đoàn (>200)" {'selected' if company.get('size')=='Tập đoàn (>200)' else ''}>Tập đoàn (>200)</option>
                            </select>
                        </div>
                    </div>

                    <div style="display:flex; gap:15px;">
                        <div style="flex:1;">
                            <label>Lĩnh vực hoạt động</label>
                            <input name="industry" value="{company.get('industry', '')}" placeholder="VD: IT Phần mềm, Marketing...">
                        </div>
                        <div style="flex:1;">
                            <label>Địa chỉ trụ sở</label>
                            <input name="address" value="{company.get('address', '')}" placeholder="VD: 123 Đường ABC, Quận 1...">
                        </div>
                    </div>

                    <label>Giới thiệu công ty</label>
                    <textarea name="description" rows="6" placeholder="Mô tả về văn hóa, lịch sử, chế độ đãi ngộ...">{company.get('description', '')}</textarea>
                </div>
            </div>

            <hr style="border:0; border-top:1px solid #eee; margin: 20px 0;">

            <div style="text-align:right;">
                <button style="width:auto; padding:12px 30px; font-size:16px; background:#16a34a;">
                    <i class="fa-solid fa-floppy-disk"></i> Lưu hồ sơ
                </button>
            </div>
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


@company_view_bp.route('/company/jobs')
def company_jobs():
    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]

    content = "<h2>📄 Tin tuyển dụng của công ty</h2>"
    try:
        comp_res = requests.get(f"{API_URL}/companies/user/{user_id}", headers=auth_headers())
        if comp_res.status_code != 200:
            return wrap_layout("<h2>⚠️ Chưa có hồ sơ công ty</h2>")      
        company = comp_res.json()        
        jobs_res = requests.get(f"{API_URL}/companies/{company['id']}/jobs", headers=auth_headers())
        my_jobs = jobs_res.json() if jobs_res.status_code == 200 else []
    except Exception as e:
        return wrap_layout("Không thể xử lý yêu cầu. Vui lòng thử lại sau.")
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
            <div style="display:flex; justify-content:space-between;">
                <h3>{escape(j['title'])}</h3>
                <span style="background:#e0f2fe; color:#0284c7; padding:4px 8px; border-radius:4px; font-size:12px; height:fit-content;">{j.get('status','OPEN')}</span>
            </div>
            <p style="white-space: pre-line; color:#555;">{escape(j['description'][:150])}...</p>
            <p><b>Ứng viên:</b> {j.get('appliedCount', 0)} / {j.get('maxApplicants', '∞')}</p>        
            <div style="margin-top:15px; border-top:1px solid #eee; padding-top:10px;">
                <a href="/company/jobs/{j['id']}/edit" style="margin-right:15px; color:#f59e0b; font-weight:bold; text-decoration:none;">
                    <i class="fa-solid fa-pen"></i> Chỉnh sửa
                </a>
                <a href="/company/jobs/{j['id']}/applications" style="color:#16a34a; font-weight:bold; text-decoration:none;">
                    <i class="fa-solid fa-users"></i> Xem ứng viên
                </a>
            </div>
        </div>
        """
    resp = make_response(wrap_layout(content))
    return resp


@company_view_bp.route('/company/jobs/create', methods=['GET', 'POST'])
def company_create_job():

    if request.method == "GET":
        csrf_token = secrets.token_hex(16)
    else:
        csrf_token = request.cookies.get("csrf_token")

    if request.method == 'POST':
        if not validate_csrf(request.form.get("csrf_token")):
            return wrap_layout("<h3>CSRF token không hợp lệ</h3>")

    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]   

    message = ""
    if request.method == 'POST':
        try:
            comp_res = requests.get(f"{API_URL}/companies/user/{user_id}", headers=auth_headers())
            company = comp_res.json()
            payload = {
                "companyId": company['id'],
                "title": request.form['title'],
                "description": request.form['description'],
                "location": request.form['location'],
                "status": "open",
                "maxApplicants": int(request.form.get("maxApplicants") or 0)
            }
            if request.form.get('has_test') == 'on':
                q_contents = request.form.getlist('q_content[]')
                questions = []
                for c in q_contents:
                    if c.strip():
                        questions.append({
                            "content": c,
                            "options": "", 
                            "correctAnswer": "" 
                        })              
                payload["test"] = {
                    "testName": request.form.get('testName', f"Test for {payload['title']}"),
                    "duration": int(request.form.get('duration') or 30),
                    "totalScore": int(request.form.get('totalScore') or 100),
                    "questions": questions
                }
            res = requests.post(f"{API_URL}/jobs/", json=payload, headers=auth_headers())      
            if res.status_code in [200, 201]:
                return redirect('/company/jobs') 
            else:
                message = "Không thể xử lý yêu cầu. Vui lòng thử lại sau."
        except Exception as e:
            message = "Không thể xử lý yêu cầu. Vui lòng thử lại sau."
    
    html = f"""
    <h2>📄 Tạo tin tuyển dụng</h2>
    <p style="color:red; font-weight:bold;">{message}</p>
    <form method="post">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        <div class="job-card">
            <h3>Thông tin công việc</h3>
            <label>Tiêu đề</label>
            <input name="title" required>
            <label>Mô tả</label>
            <textarea name="description" required></textarea>
            <label>Địa điểm</label>
            <input name="location">
            <label>Số ứng viên tối đa</label>
            <input name="maxApplicants" type="number" min="1">
        </div>
        <div class="job-card" style="border-left: 6px solid #2563eb; background:#f8fafc;">
            <label style="display:flex; align-items:center; cursor:pointer; color:#2563eb;">
                <input type="checkbox" name="has_test" id="chkTest" onclick="toggleTestForm()" style="width:auto; margin-right:10px;">
                <b>Kèm bài kiểm tra năng lực (Tự luận)?</b>
            </label>
            <div id="test-form" style="display:none; margin-top:15px; border-top:1px solid #ddd; padding-top:10px;">
                <label>Tên bài kiểm tra</label>
                <input name="testName">
                <div style="display:flex; gap:15px;">
                    <div style="flex:1;"><label>Thời gian (phút)</label><input type="number" name="duration" value="30"></div>
                    <div style="flex:1;"><label>Tổng điểm</label><input type="number" name="totalScore" value="100"></div>
                </div>
                <label>Danh sách câu hỏi :</label>
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
            div.innerHTML = `<div style="font-weight:bold; font-size:13px; margin-bottom:5px;">Câu hỏi mới (Tự luận)</div>
            <textarea name="q_content[]" placeholder="Nhập nội dung câu hỏi..." required style="margin-bottom:5px; width:100%;" rows="3"></textarea>
            <button type="button" onclick="this.parentElement.remove()" style="background:#ef4444; width:auto; padding:4px 10px; font-size:12px; margin-top:5px;">Xóa</button>`;
            document.getElementById("questions-container").appendChild(div);
        }}
    </script>
    """
    resp = make_response(wrap_layout(html))
    resp.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=True,
        samesite="Lax",
        secure=request.is_secure
    )
    return resp


@company_view_bp.route('/company/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def company_edit_job(job_id):

    if request.method == "GET":
        csrf_token = secrets.token_hex(16)
    else:
        csrf_token = request.cookies.get("csrf_token")

    if request.method == 'POST':
        if not validate_csrf(request.form.get("csrf_token")):
            return wrap_layout("<h3>CSRF token không hợp lệ</h3>")

    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]   

    message = ""    
    try:
        comp = requests.get(f"{API_URL}/companies/user/{user_id}", headers=auth_headers()).json()
        company_id = comp['id']
        job_res = requests.get(f"{API_URL}/jobs/{job_id}", headers=auth_headers())
        if job_res.status_code != 200: return wrap_layout("<h2>❌ Không tìm thấy Job</h2>")
        job = job_res.json()
        if job.get('companyId') != company_id: return wrap_layout("<h2>⛔ Bạn không có quyền</h2>")        
        test_res = requests.get(f"{API_URL}/jobs/{job_id}/tests", headers=auth_headers())
        tests = test_res.json() if test_res.status_code == 200 else []
        current_test = tests[0] if tests else None
        test_questions = []
        if current_test:
             q_res = requests.get(f"{API_URL}/tests/{current_test['id']}", headers=auth_headers())
             if q_res.status_code == 200: test_questions = q_res.json().get('questions', [])
    except Exception as e:
        return wrap_layout(f"<h2>Lỗi tải dữ liệu: {e}</h2>")
    if request.method == 'POST':
        try:
            payload = {
                "companyId": company_id,
                "title": request.form['title'],
                "description": request.form['description'],
                "location": request.form['location'],
                "maxApplicants": int(request.form.get("maxApplicants") or 0)
            }
            if request.form.get('has_test') == 'on':
                q_contents = request.form.getlist('q_content[]')
                questions_list = []
                for c in q_contents:
                    if c.strip(): questions_list.append({"content": c, "options": "", "correctAnswer": ""})
                payload["test"] = {
                    "testName": request.form['testName'],
                    "duration": int(request.form['duration'] or 30),
                    "totalScore": int(request.form['totalScore'] or 100),
                    "questions": questions_list
                }
            res = requests.put(f"{API_URL}/jobs/{job_id}", json=payload, headers=auth_headers())
            if res.status_code == 200: return redirect('/company/jobs')
            else: message = f"Lưu thất bại: {res.text}"
        except Exception as e:
            message = "Không thể xử lý yêu cầu. Vui lòng thử lại sau."

    questions_json = json.dumps(test_questions) if current_test else "[]"
    has_test_checked = "checked" if current_test else ""
    display_test_form = "block" if current_test else "none"

    html = f"""
    <h2>✏️ Chỉnh sửa tin tuyển dụng</h2>
    <p style="color:red">{message}</p>
    <a href="/company/jobs">← Quay lại danh sách</a>
    <form method="post" style="margin-top:20px;">
        <div class="job-card">
            <h3>Thông tin công việc</h3>
            <label>Tiêu đề</label><input name="title" required value="{job['title']}">
            <label>Mô tả</label><textarea name="description" required style="min-height:120px;">{job['description']}</textarea>
            <label>Địa điểm</label><input name="location" value="{job.get('location', '')}">
            <label>Số ứng viên tối đa</label>
            <input name="maxApplicants" type="number" min="1" value="{job.get('maxApplicants', 0)}">
        </div>
        <div class="job-card" style="border-left: 6px solid #2563eb; background:#f0f9ff;">
            <label style="display:flex; align-items:center; cursor:pointer; color:#2563eb; margin-bottom:15px;">
                <input type="checkbox" name="has_test" id="chkTest" onclick="toggleTestForm()" {has_test_checked} style="width:auto; margin-right:10px;"><b>Kèm bài kiểm tra năng lực (Tự luận)?</b>
            </label>
            <div id="test-form" style="display:{display_test_form};">
                <label>Tên bài kiểm tra</label><input name="testName" value="{current_test.get('testName', '') if current_test else ''}">
                <div style="display:flex; gap:15px;">
                    <div style="flex:1;"><label>Thời gian</label><input type="number" name="duration" value="{current_test.get('duration', 30) if current_test else 30}"></div>
                    <div style="flex:1;"><label>Tổng điểm</label><input type="number" name="totalScore" value="{current_test.get('totalScore', 100) if current_test else 100}"></div>
                </div>
                <h4 style="margin-top:20px;">Danh sách câu hỏi :</h4>
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
        function addQuestionInput(content='') {{
            var container = document.getElementById("questions-container");
            var div = document.createElement("div");
            div.style.marginBottom = "15px"; div.style.padding = "15px"; div.style.background = "white"; div.style.border = "1px solid #cbd5e1";
            div.innerHTML = `<div style="font-weight:bold; font-size:13px; margin-bottom:8px;">Câu hỏi </div>
            <textarea name="q_content[]" placeholder="Nội dung câu hỏi..." required style="margin-bottom:8px; width:100%;" rows="3">${{content}}</textarea>
            <button type="button" onclick="this.parentElement.remove()" style="background:#ef4444; width:auto; padding:4px 10px; font-size:11px; margin-top:5px;">Xóa</button>`;
            container.appendChild(div);
        }}
        window.onload = function() {{
            if (existingQuestions.length > 0) {{ existingQuestions.forEach(q => {{ addQuestionInput(q.content.replace(/"/g, '&quot;')); }}); }}
            else if (document.getElementById("chkTest").checked) {{ addQuestionInput(); }}
        }};
    </script>
    """
    resp = make_response(wrap_layout(html))
    resp.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=True,
        samesite="Lax",
        secure=request.is_secure
    )
    return resp


@company_view_bp.route('/company/applications')
def company_applications():
    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]   

    try:
        user_id = user["id"]
        comp_res = requests.get(f"{API_URL}/companies/user/{user_id}", headers=auth_headers())
        company = comp_res.json()
        apps_res = requests.get(f"{API_URL}/companies/{company['id']}/applications", headers=auth_headers())
        apps = apps_res.json() if apps_res.status_code == 200 else []
    except:
        apps = []

    content = "<h2>📥 Danh sách hồ sơ ứng tuyển</h2>"

    if not apps:
        content += "<p style='color:#666;'>Chưa có hồ sơ nào.</p>"
    else:
        content += """
        <table style="width:100%; border-collapse:collapse; background:white; margin-top:20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-radius:8px; overflow:hidden;">
            <thead style="background:#f1f5f9; border-bottom:2px solid #e2e8f0;">
                <tr>
                    <th style="padding:15px; text-align:left;">Ứng viên</th>
                    <th style="padding:15px; text-align:left;">Vị trí</th>
                    <th style="padding:15px;">Điểm</th>
                    <th style="padding:15px;">Trạng thái</th>
                    <th style="padding:15px; text-align:right;">Hành động</th>
                </tr>
            </thead>
            <tbody>
        """

        for a in apps:
            score_display = f"<b>{a['testScore']}</b>" if a['testScore'] != "N/A" else "--"

            content += f"""
            <tr style="border-bottom:1px solid #eee;">
                <td style="padding:15px;">
                    <b>{escape(a['studentName'])}</b>
                </td>
                <td style="padding:15px;">
                    {a['jobTitle']}
                </td>
                <td style="padding:15px; text-align:center;">
                    {score_display}
                </td>
                <td style="padding:15px; text-align:center;">
                    <span style="background:#e0f2fe; color:#0369a1; padding:4px 8px; border-radius:12px; font-size:12px; font-weight:bold;">{a['status']}</span>
                </td>
                <td style="padding:15px; text-align:right;">
                    <a href="/company/applications/{a['applicationId']}/cv"
                       style="margin-right:5px; background:#2563eb; color:white; padding:6px 10px; border-radius:4px; text-decoration:none; font-size:13px;">
                        <i class="fa-solid fa-eye"></i> Xem CV
                    </a>

                    <a href="/company/applications/{a['applicationId']}/evaluate"
                       style="background:#0f172a; color:white; padding:6px 10px; border-radius:4px; text-decoration:none; font-size:13px;">
                        <i class="fa-solid fa-pen-to-square"></i> Đánh giá
                    </a>
                </td>
            </tr>
            """

        content += "</tbody></table>"

    resp = make_response(wrap_layout(content))
    return resp


@company_view_bp.route('/company/applications/<int:app_id>/evaluate', methods=['GET', 'POST'])
def company_evaluate_application(app_id):

    if request.method == "GET":
        csrf_token = secrets.token_hex(16)
    else:
        csrf_token = request.cookies.get("csrf_token")

    if request.method == 'POST':
        if not validate_csrf(request.form.get("csrf_token")):
            return wrap_layout("<h3>CSRF token không hợp lệ</h3>")

    if not check_application_owner(app_id):
        return wrap_layout("<h2>Bạn không có quyền truy cập hồ sơ này</h2>")

    user = require_company_view()
    if not user:
        return redirect('/login')

    if request.method == 'POST':
        payload = {
            "nextStatus": request.form.get('action'),
            "skillScore": request.form.get('skillScore'),
            "peerReview": request.form.get('peerReview'),
            "improvement": request.form.get('improvement'),
            "interviewTime": request.form.get('interviewTime'),
            "interviewLocation": request.form.get('interviewLocation'),
            "interviewNote": request.form.get('interviewNote'),
            "interviewFeedback": request.form.get('interviewFeedback'),
            "interviewRating": request.form.get('interviewRating')
        }

        requests.post(
            f"{API_URL}/applications/{app_id}/evaluate",
            json=payload,
            headers=auth_headers()
        )


        return redirect('/company/applications')
    
    res = requests.get(f"{API_URL}/applications/{app_id}/test-detail", headers=auth_headers())
    if res.status_code != 200: return wrap_layout("Lỗi tải dữ liệu")
    data = res.json()
    status = data.get("status", "pending") 
    
    test_html = ""
    if data.get("hasTest") and data.get("submitted"):
        rows = ""
        for idx, item in enumerate(data['details'], 1):
             rows += f"<div style='margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;'><b>Câu {idx}:</b> {item['question']}<br><i>TL: {item['answer']}</i></div>"
        test_html = f"<div class='job-card' style='border-left:6px solid #f59e0b;'><h3>📝 Bài test (Điểm: {data['score']})</h3>{rows}</div>"

    form_html = ""

    if status in ['pending', 'testing']:
        form_html = f"""
        <div class="job-card" style="border-left:6px solid #8b5cf6;">
            <h3>🔍 Vòng 1: Sơ tuyển hồ sơ</h3>
            <form method="post">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <div style="margin-bottom:20px;">
                    <label>Điểm hồ sơ</label><input type="number" name="skillScore">
                    <label>Nhận xét</label><textarea name="peerReview"></textarea>
                    <label>Cần cải thiện</label><textarea name="improvement"></textarea>
                </div>
                <div style="background:#f0fdf4; padding:15px; border-radius:6px; margin-bottom:20px;">
                    <h4 style="margin:0 0 10px 0; color:#166534;">📅 Lên lịch phỏng vấn</h4>
                    <div style="display:flex; gap:10px;">
                        <input type="datetime-local" name="interviewTime" style="flex:1">
                        <input name="interviewLocation" placeholder="Địa điểm / Link Online" style="flex:2">
                    </div>
                    <input name="interviewNote" placeholder="Ghi chú dặn dò...">
                </div>
                <div style="display:flex; gap:10px;">
                    <button name="action" value="interview" style="background:#2563eb;">✅ Duyệt & Mời PV</button>
                    <button name="action" value="rejected" style="background:#ef4444;">❌ Loại hồ sơ</button>
                </div>
            </form>
        </div>
        """
    elif status == 'interview':
        form_html = f"""
        <div class="job-card" style="border-left:6px solid #ec4899;">
            <h3>🎤 Vòng 2: Đánh giá Phỏng vấn</h3>
            <p>Hồ sơ này đang trong quá trình phỏng vấn. Hãy nhập kết quả sau khi gặp ứng viên.</p>
            <form method="post">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <label>Nhận xét buổi phỏng vấn (Interview Feedback)</label>
                <textarea name="interviewFeedback" rows="5" required placeholder="Ứng viên trả lời thế nào? Thái độ ra sao?"></textarea>
                
                <label>Điểm đánh giá (1 - 5)</label>
                <select name="interviewRating">
                    <option value="5">⭐⭐⭐⭐⭐ (Xuất sắc)</option>
                    <option value="4">⭐⭐⭐⭐ (Tốt)</option>
                    <option value="3">⭐⭐⭐ (Khá)</option>
                    <option value="2">⭐⭐ (Trung bình)</option>
                    <option value="1">⭐ (Kém)</option>
                </select>

                <div style="display:flex; gap:10px; margin-top:20px;">
                    <button name="action" value="offered" style="background:#16a34a;">💌 Gửi Offer (Đậu)</button>
                    <button name="action" value="rejected" style="background:#ef4444;">❌ Từ chối (Trượt)</button>
                </div>
            </form>
        </div>
        """
    else:
        form_html = f"<div class='job-card'><h3>🏁 Hồ sơ đã đóng</h3><p>Trạng thái hiện tại: <b>{status.upper()}</b></p></div>"

    html = f"<h2>⚖️ Quy trình tuyển dụng</h2>{test_html}{form_html}"

    resp = make_response(wrap_layout(html))
    resp.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=True,
        samesite="Lax",
        secure=request.is_secure
    )
    return resp
    

@company_view_bp.route('/company/jobs/<int:job_id>/applications')
def company_view_applicants(job_id):
    user = require_company_view()
    if not user:
        return redirect('/login')

    try: apps = requests.get(f"{API_URL}/jobs/{job_id}/applications", headers=auth_headers()).json()
    except: apps = []
    content = f"<h2>📥 Ứng viên cho Job #{job_id}</h2>"
    for a in apps:
        content += f"""<div class="job-card"><b>{a['studentName']}</b><br>Trạng thái: {a['status']}<br><a href="/company/applications/{a['applicationId']}/cv">📄 Xem CV</a></div>"""
    resp = make_response(wrap_layout(content))
    return resp


@company_view_bp.route("/company/applications/<int:app_id>/cv")
def company_view_cv(app_id):
    
    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]

    
    if not check_application_owner(app_id):
        return wrap_layout("<h2>⛔ Bạn không có quyền truy cập hồ sơ này</h2>")

    res = requests.get(f"{API_URL}/companies/applications/{app_id}/cv", headers=auth_headers())

    if res.status_code != 200:
        return wrap_layout("<h3>❌ Không thể tải thông tin hồ sơ</h3>")

    data = res.json()

    skills_html = ""
    if data.get("skills") and isinstance(data["skills"], list):
        for s in data["skills"]:
            skills_html += f'<span class="badge-skill">{s["name"]} (Lv.{s["level"]})</span>'
    else:
        skills_html = '<span style="color:#999; font-style:italic;">Chưa cập nhật kỹ năng.</span>'

    dob = data.get("dob") if data.get("dob") else "Chưa cập nhật"
    cccd = data.get("cccd") if data.get("cccd") else "Chưa cập nhật"
    education = data.get("educationLevel") if data.get("educationLevel") else "Chưa cập nhật"
    degrees = data.get("degrees") if data.get("degrees") else "Chưa cập nhật"
    about = data.get("about") if data.get("about") else "Ứng viên chưa viết giới thiệu."
    portfolio_url = data.get("portfolioUrl")

    content = f"""
    <h2>📄 Chi tiết hồ sơ ứng viên</h2>
    <a href="/company/applications">← Quay lại danh sách</a>

    <div class="job-card">
        <div class="cv-container">
            <div class="cv-left">
                <img src="https://ui-avatars.com/api/?name={data.get('studentName', 'User')}&size=128&background=random&color=fff&rounded=true" 
                     style="border-radius:50%; margin-bottom:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" alt="Avatar">
                
                <h2 style="color:#1e40af; margin-bottom:5px;">{data.get('studentName', 'N/A')}</h2>
                <p style="color:#64748b; font-weight:bold; margin-top:0;">{data.get('major', 'Chưa có ngành')}</p>
                
                <hr style="border:0; border-top:1px solid #e2e8f0; margin: 20px 0;">
                
                <p style="font-size:13px; color:#64748b;">Vị trí ứng tuyển</p>
                <p style="font-weight:bold; color:#0f172a;">{data.get('jobTitle', 'N/A')}</p>
                
                <div style="margin-top:30px;">
                    <a href="{data.get('cvUrl', '#')}" target="_blank">
                        <button style="background:#dc2626; margin-bottom:10px;">
                            <i class="fa-solid fa-file-pdf"></i> Xem CV Gốc (PDF)
                        </button>
                    </a>
                    {f'<a href="{portfolio_url}" target="_blank"><button style="background:#334155;"><i class="fa-solid fa-globe"></i> Xem Portfolio</button></a>' if portfolio_url else ''}
                </div>
            </div>

            <div class="cv-right">
                <div class="section-title"><i class="fa-solid fa-user"></i> Thông tin cá nhân</div>
                <div style="display:flex; gap:20px; margin-bottom:15px;">
                    <div style="flex:1;"><strong>📅 Ngày sinh:</strong> {dob}</div>
                    <div style="flex:1;"><strong>🆔 CCCD:</strong> {cccd}</div>
                </div>

                <div class="section-title"><i class="fa-solid fa-graduation-cap"></i> Học vấn & Bằng cấp</div>
                <p><strong>🎓 Trình độ:</strong> {education}</p>
                <p><strong>📜 Chứng chỉ:</strong> {degrees}</p>

                <div class="section-title"><i class="fa-solid fa-star"></i> Kỹ năng chuyên môn</div>
                <div style="margin-bottom:15px;">
                    {skills_html}
                </div>

                <div class="section-title"><i class="fa-solid fa-quote-left"></i> Giới thiệu bản thân</div>
                <div style="background:#f8fafc; padding:15px; border-radius:6px; font-style:italic; color:#475569; border-left:4px solid #cbd5e1;">
                    "{escape(about)}"
                </div>

                <div style="margin-top:30px; text-align:right;">
                     <a href="/company/applications/{app_id}/evaluate">
                        <button style="width:auto; padding:10px 20px; background:#16a34a;">
                            <i class="fa-solid fa-check-to-slot"></i> Đánh giá / Phỏng vấn
                        </button>
                     </a>
                </div>
            </div>
        </div>
    </div>
    """

    return wrap_layout(content)