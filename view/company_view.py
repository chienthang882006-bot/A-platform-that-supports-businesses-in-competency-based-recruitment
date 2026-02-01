from flask import Blueprint, request, redirect, make_response
from markupsafe import escape
from typing import cast, Any
import requests
import json
import secrets
import jwt
from datetime import datetime
from utils import wrap_layout, API_URL, get_current_user_from_jwt, auth_headers
from database import db_session
from models.user_models import Company, CompanyProfile, Student
from models.job_models import Job, SkillTest, Question
from models.app_models import Application, TestResult, Evaluation, Interview, InterviewFeedback, Notification, ApplicationStatus
from sqlalchemy import func, cast, String
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
def get_company_profile_missing_fields_by_user(user_id: int):
    company = db_session.query(Company).filter(Company.userId == user_id).first()
    if not company:
        return ["company"]

    # Bạn có thể chỉnh danh sách bắt buộc ở đây
    required_company = {"companyName": "Tên công ty"}

    required_profile = {
        "logoUrl": "Logo (URL)",
        "website": "Website",
        "industry": "Lĩnh vực",
        "size": "Quy mô",
        "address": "Địa chỉ",
        "description": "Giới thiệu",
    }

    missing = []

    # check Company
    for attr, label in required_company.items():
        val = getattr(company, attr, None)
        if not val or str(val).strip() == "":
            missing.append(label)

    # check CompanyProfile
    prof = db_session.query(CompanyProfile).filter(CompanyProfile.companyId == company.id).first()
    if not prof:
        missing.extend(list(required_profile.values()))
        return missing

    for attr, label in required_profile.items():
        val = getattr(prof, attr, None)
        if not val or str(val).strip() == "":
            missing.append(label)

    return missing


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
    # 1. Kiểm tra đăng nhập
    user = require_company_view()
    if not user:
        return redirect('/login')

    # 2. Xử lý CSRF Token
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_hex(16)

    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            return wrap_layout("<h3 style='color:red'>❌ CSRF token không hợp lệ</h3>")

    user_id = user["id"]   
    message = ""

    # 3. XỬ LÝ LƯU (POST)
    if request.method == 'POST':
        try:
            # Lấy thông tin Company từ DB
            company = db_session.query(Company).filter(Company.userId == user_id).first()
            
            if company:
                # Cập nhật tên công ty
                # FIX: Bỏ cast(), gán trực tiếp giá trị lấy từ form
                if request.form.get("companyName"):
                    company.companyName = request.form.get("companyName") or ""

                # Tìm hoặc tạo Profile
                profile = db_session.query(CompanyProfile).filter(CompanyProfile.companyId == company.id).first()
                if not profile:
                    profile = CompanyProfile(companyId=company.id)
                    db_session.add(profile)
                    db_session.flush()

                # Cập nhật thông tin chi tiết (Xử lý None thành chuỗi rỗng)
                # FIX: Bỏ cast(Any, ...), chỉ cần lấy value hoặc chuỗi rỗng
                profile.website = request.form.get("website") or ""
                profile.address = request.form.get("address") or ""
                profile.industry = request.form.get("industry") or ""
                profile.size = request.form.get("size") or ""
                profile.logoUrl = request.form.get("logoUrl") or ""
                profile.description = request.form.get("description") or ""

                db_session.commit()
                message = "<div style='background:#dcfce7; color:#166534; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #bbf7d0; font-weight:bold;'>✅ Đã lưu hồ sơ thành công!</div>"
            else:
                message = "<div style='color:red; margin-bottom:15px;'>Lỗi: Không tìm thấy thông tin công ty.</div>"

        except Exception as e:
            db_session.rollback()
            print(f"Error saving profile: {e}")
            message = f"<div style='color:red; margin-bottom:15px;'>Lỗi kết nối CSDL: {str(e)}</div>"

    # 4. LẤY DỮ LIỆU HIỂN THỊ (GET)
    company_data = {}
    try:
        comp = db_session.query(Company).filter(Company.userId == user_id).first()
        if comp:
            prof = db_session.query(CompanyProfile).filter(CompanyProfile.companyId == comp.id).first()
            company_data = {
                "companyName": comp.companyName,
                "logoUrl": (prof.logoUrl or "") if prof else "",
                "website": (prof.website or "") if prof else "",
                "size": (prof.size or "") if prof else "",
                "industry": (prof.industry or "") if prof else "",
                "address": (prof.address or "") if prof else "",
                "description": (prof.description or "") if prof else ""
            }
    except Exception as e:
        print(f"Error loading profile: {e}")

    # 5. RENDER GIAO DIỆN
    content = f"""
    <h2>⚙️ Hồ sơ doanh nghiệp</h2>
    {message}
    
    <div class="job-card">
        <form method="post">
            <input type="hidden" name="csrf_token" value="{csrf_token}">
            <div style="display:flex; gap:30px;">
                <div style="flex:1; text-align:center;">
                    <div style="border: 2px dashed #cbd5e1; border-radius: 12px; padding: 10px; margin-bottom: 15px;">
                        <img src="{company_data.get('logoUrl') or 'https://via.placeholder.com/150?text=No+Logo'}" 
                             style="width:100%; height:150px; object-fit:contain; border-radius:8px;"
                             onerror="this.src='https://via.placeholder.com/150?text=Error'">
                    </div>
                    <label style="text-align:left; font-size:13px;">Link Logo (URL ảnh)</label>
                    <input name="logoUrl" value="{company_data.get('logoUrl', '')}" placeholder="https://example.com/logo.png">
                </div>

                <div style="flex:3;">
                    <label>Tên công ty <span style="color:red">*</span></label>
                    <input name="companyName" value="{escape(company_data.get('companyName', ''))}" required style="font-weight:bold;">
                    
                    <div style="display:flex; gap:15px;">
                        <div style="flex:1;">
                            <label>Website</label>
                            <input name="website" value="{company_data.get('website', '')}" placeholder="https://mycompany.com">
                        </div>
                        <div style="flex:1;">
                            <label>Quy mô nhân sự</label>
                            <select name="size">
                                <option value="">-- Chọn quy mô --</option>
                                <option value="Startup (1-10)" {'selected' if company_data.get('size')=='Startup (1-10)' else ''}>Startup (1-10)</option>
                                <option value="Vừa (10-50)" {'selected' if company_data.get('size')=='Vừa (10-50)' else ''}>Vừa (10-50)</option>
                                <option value="Lớn (50-200)" {'selected' if company_data.get('size')=='Lớn (50-200)' else ''}>Lớn (50-200)</option>
                                <option value="Tập đoàn (>200)" {'selected' if company_data.get('size')=='Tập đoàn (>200)' else ''}>Tập đoàn (>200)</option>
                            </select>
                        </div>
                    </div>

                    <div style="display:flex; gap:15px;">
                        <div style="flex:1;">
                            <label>Lĩnh vực hoạt động</label>
                            <input name="industry" value="{company_data.get('industry', '')}" placeholder="VD: IT Phần mềm, Marketing...">
                        </div>
                        <div style="flex:1;">
                            <label>Địa chỉ trụ sở</label>
                            <input name="address" value="{company_data.get('address', '')}" placeholder="VD: 123 Đường ABC, Quận 1...">
                        </div>
                    </div>

                    <label>Giới thiệu công ty</label>
                    <textarea name="description" rows="6" placeholder="Mô tả về văn hóa, lịch sử, chế độ đãi ngộ...">{company_data.get('description', '')}</textarea>
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

    db_session.remove()
    user_id = user["id"]
    content = "<h2>📄 Tin tuyển dụng của công ty</h2>"

    try:
        # 1) Lấy thông tin công ty
        db_session.expire_all()
        company = db_session.query(Company).filter(Company.userId == user_id).first()

        # Nếu chưa có công ty -> Hiển thị thông báo và nút tạo hồ sơ
        if not company:
            return wrap_layout("""
                <div style="text-align:center; padding:50px;">
                    <h2 style="color:#f59e0b;">⚠️ Chưa có thông tin công ty</h2>
                    <p>Hệ thống không tìm thấy thông tin công ty của bạn.</p>
                    <p>Vui lòng cập nhật hồ sơ trước khi đăng tuyển.</p>
                    <a href="/company/profile" style="background:#16a34a; color:white; padding:10px 20px; border-radius:5px; text-decoration:none; font-weight:bold;">
                        👉 Tạo hồ sơ ngay
                    </a>
                </div>
            """)

        # 2) Check hồ sơ trước khi cho tạo job  ✅ (NẰM TRONG TRY)
        missing_fields = get_company_profile_missing_fields_by_user(user_id)

        if missing_fields:
            content += f"""
            <div class="job-card" style="border-left:6px solid #ef4444; background:#fff5f5;">
                <h3 style="margin:0; color:#b91c1c;">⚠️ Vui lòng nhập đầy đủ thông tin trước khi tạo job</h3>
                <p style="margin:8px 0 0; color:#7f1d1d;">
                    Thiếu: <b>{escape(", ".join(missing_fields))}</b>
                </p>
                <div style="margin-top:12px;">
                    <a href="/company/profile"
                       style="display:inline-block; background:#16a34a; color:white; padding:10px 16px; border-radius:6px; text-decoration:none; font-weight:bold;">
                        👉 Cập nhật hồ sơ doanh nghiệp
                    </a>
                </div>
            </div>
            """
        else:
            content += """
            <a href="/company/jobs/create" style="display:inline-block; margin:10px 0; padding:10px 14px; background:#16a34a; color:white; border-radius:6px; text-decoration:none; font-weight:bold;">
                ➕ Tạo Job mới
            </a>
            """

        # 3) Lấy danh sách Job (vẫn cho xem danh sách dù thiếu hồ sơ)
        my_jobs = db_session.query(Job).filter(Job.companyId == company.id).order_by(Job.createdAt.desc()).all()

        if not my_jobs:
            content += "<p>Chưa có tin tuyển dụng nào. Hãy tạo tin đầu tiên!</p>"

        # 4) Render danh sách job
        for j in my_jobs:
            applied_count = db_session.query(func.count(Application.id)).filter(Application.jobId == j.id).scalar()
            content += f"""
            <div class="job-card">
                <div style="display:flex; justify-content:space-between;">
                    <h3>{escape(j.title)}</h3>
                    <span style="background:#e0f2fe; color:#0284c7; padding:4px 8px; border-radius:4px; font-size:12px; height:fit-content;">{j.status}</span>
                </div>
                <p style="white-space: pre-line; color:#555;">{escape(j.description[:150])}...</p>
                <p><b>Ứng viên:</b> {applied_count} / {j.maxApplicants if j.maxApplicants > 0 else '∞'}</p>
                <div style="margin-top:15px; border-top:1px solid #eee; padding-top:10px;">
                    <a href="/company/jobs/{j.id}/edit" style="margin-right:15px; color:#f59e0b; font-weight:bold; text-decoration:none;">
                        <i class="fa-solid fa-pen"></i> Chỉnh sửa
                    </a>
                    <a href="/company/jobs/{j.id}/applications" style="color:#16a34a; font-weight:bold; text-decoration:none;">
                        <i class="fa-solid fa-users"></i> Xem ứng viên
                    </a>
                </div>
            </div>
            """

    except Exception as e:
        print(f"Error loading jobs: {e}")
        return wrap_layout(f"<h3 style='color:red'>Lỗi tải dữ liệu: {str(e)}</h3>")

    resp = make_response(wrap_layout(content))
    return resp



@company_view_bp.route('/company/jobs/create', methods=['GET', 'POST'])
def company_create_job():
    # 1. Kiểm tra CSRF & User
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_hex(16)

    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            return wrap_layout("<h3 style='color:red'>❌ CSRF token không hợp lệ</h3>")

    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]
    message = ""

    # ✅ GUARD (chặn luôn cả GET/POST nếu thiếu hồ sơ)
    missing_fields = get_company_profile_missing_fields_by_user(user_id)
    if missing_fields:
        return wrap_layout(f"""
            <div style="text-align:center; padding:50px;">
                <h2 style="color:#ef4444;">⚠️ Vui lòng nhập đầy đủ thông tin trước khi tạo job</h2>
                <p>Bạn đang thiếu: <b>{escape(", ".join(missing_fields))}</b></p>
                <a href="/company/profile"
                   style="background:#16a34a; color:white; padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:bold;">
                    👉 Cập nhật hồ sơ doanh nghiệp
                </a>
            </div>
        """)

    # 2. XỬ LÝ LƯU JOB (TRỰC TIẾP DB)
    if request.method == 'POST':
        try:
            # Lấy thông tin công ty
            company = db_session.query(Company).filter(Company.userId == user_id).first()
            if not company:
                return wrap_layout("Lỗi: Không tìm thấy thông tin công ty.")

            # Tạo Job Mới
            new_job = Job(
                companyId=company.id,
                title=request.form['title'],
                description=request.form['description'],
                location=request.form.get('location', ''),
                status="open",
                maxApplicants=int(request.form.get("maxApplicants") or 0)
            )
            db_session.add(new_job)
            db_session.flush()  # Lấy ID của Job vừa tạo

            # Xử lý Bài Test (Nếu có tích chọn)
            if request.form.get('has_test') == 'on':
                new_test = SkillTest(
                    jobId=new_job.id,
                    testName=request.form.get('testName', f"Test for {new_job.title}"),
                    duration=int(request.form.get('duration') or 30),
                    totalScore=int(request.form.get('totalScore') or 100)
                )
                db_session.add(new_test)
                db_session.flush()

                # Lưu danh sách câu hỏi
                q_contents = request.form.getlist('q_content[]')
                for c in q_contents:
                    if c and c.strip():
                        db_session.add(Question(
                            testId=new_test.id,
                            content=c.strip(),
                            options="",
                            correctAnswer=""
                        ))

            db_session.commit()
            return redirect('/company/jobs')

        except Exception as e:
            db_session.rollback()
            print(f"Error creating job: {e}")
            message = f"Lỗi hệ thống: {str(e)}"
    
    # 3. RENDER GIAO DIỆN (Giữ nguyên phần HTML)
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
    # 1. Setup CSRF Token
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_hex(16)

    # 2. Validate CSRF khi POST
    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            return wrap_layout("<h3 style='color:red'>❌ CSRF token không hợp lệ</h3>")

    # 3. Kiểm tra quyền đăng nhập
    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]   
    message = ""    

    # --- PHẦN 1: XỬ LÝ LƯU DỮ LIỆU (POST) ---
    # (Đoạn này bị thiếu trong file cũ của bạn)
    if request.method == 'POST':
        try:
            # Chuẩn bị dữ liệu gửi lên API
            payload = {
                "title": request.form['title'],
                "description": request.form['description'],
                "location": request.form['location'],
                "maxApplicants": int(request.form.get("maxApplicants") or 0),
                "status": "open" 
            }

            # Xử lý bài Test (nếu có)
            if request.form.get('has_test') == 'on':
                q_contents = request.form.getlist('q_content[]')
                questions_list = []
                for c in q_contents:
                    if c.strip():
                        questions_list.append({
                            "content": c.strip(), 
                            "options": "", 
                            "correctAnswer": ""
                        })
                
                payload["test"] = {
                    "testName": request.form['testName'],
                    "duration": int(request.form['duration'] or 30),
                    "totalScore": int(request.form['totalScore'] or 100),
                    "questions": questions_list
                }
            
            # Gọi API cập nhật (PUT)
            # Lưu ý: requests.put sẽ tự động dùng 'Content-Type: application/json' khi dùng tham số json=...
            res = requests.put(f"{API_URL}/jobs/{job_id}", json=payload, headers=auth_headers())
            
            if res.status_code == 200:
                # Xóa cache session cũ để trang danh sách cập nhật ngay
                db_session.remove() 
                return redirect('/company/jobs')
            else:
                message = f"<span style='color:red'>❌ Lưu thất bại: {res.text}</span>"
        
        except Exception as e:
            print(f"Error saving job: {e}")
            message = f"<span style='color:red'>❌ Lỗi hệ thống: {str(e)}</span>"

    # --- PHẦN 2: LẤY DỮ LIỆU ĐỂ HIỂN THỊ (GET) ---
    db_session.expire_all()
    current_test = None
    test_questions = []
    job = {}
    
    try:
        # A. Lấy thông tin Company để check quyền
        comp_res = requests.get(f"{API_URL}/companies/user/{user_id}", headers=auth_headers())
        if comp_res.status_code != 200:
             return wrap_layout(f"<h2>❌ Lỗi: Không lấy được thông tin công ty (Code {comp_res.status_code})</h2>")
        
        comp = comp_res.json()
        company_id = comp.get('id')
        
        # B. Lấy thông tin Job
        job_res = requests.get(f"{API_URL}/jobs/{job_id}", headers=auth_headers())
        if job_res.status_code != 200: 
            return wrap_layout("<h2>❌ Không tìm thấy Job</h2>")
        
        job = job_res.json()
        if job.get('companyId') != company_id: 
            return wrap_layout("<h2>⛔ Bạn không có quyền chỉnh sửa Job này</h2>")        
        
        # C. Lấy thông tin bài Test (Dùng API /test-info mới)
        test_res = requests.get(f"{API_URL}/jobs/{job_id}/test-info", headers=auth_headers())
        if test_res.status_code == 200 and test_res.content:
            data = test_res.json()
            if data:
                current_test = data
                test_questions = data.get('questions', [])

    except Exception as e:
        print(f"Edit Job View Error: {e}")
        return wrap_layout(f"<h2>Lỗi tải dữ liệu: {str(e)}</h2>")

    # --- PHẦN 3: RENDER GIAO DIỆN ---
    questions_json = json.dumps(test_questions) if current_test else "[]"
    has_test_checked = "checked" if current_test else ""
    display_test_form = "block" if current_test else "none"

    html = f"""
    <h2>✏️ Chỉnh sửa tin tuyển dụng</h2>
    <p>{message}</p>
    <a href="/company/jobs">← Quay lại danh sách</a>
    
    <form method="post" style="margin-top:20px;">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        
        <div class="job-card">
            <h3>Thông tin công việc</h3>
            <label>Tiêu đề</label>
            <input name="title" required value="{escape(job.get('title', ''))}">
            
            <label>Mô tả</label>
            <textarea name="description" required style="min-height:120px;">{escape(job.get('description', ''))}</textarea>
            
            <label>Địa điểm</label>
            <input name="location" value="{escape(job.get('location', ''))}">
            
            <label>Số ứng viên tối đa</label>
            <input name="maxApplicants" type="number" min="1" value="{job.get('maxApplicants', 0)}">
        </div>

        <div class="job-card" style="border-left: 6px solid #2563eb; background:#f0f9ff;">
            <label style="display:flex; align-items:center; cursor:pointer; color:#2563eb; margin-bottom:15px;">
                <input type="checkbox" name="has_test" id="chkTest" onclick="toggleTestForm()" {has_test_checked} style="width:auto; margin-right:10px;">
                <b>Kèm bài kiểm tra năng lực (Tự luận)?</b>
            </label>
            
            <div id="test-form" style="display:{display_test_form};">
                <label>Tên bài kiểm tra</label>
                <input name="testName" value="{escape(current_test.get('testName', '') if current_test else '')}">
                
                <div style="display:flex; gap:15px;">
                    <div style="flex:1;">
                        <label>Thời gian (phút)</label>
                        <input type="number" name="duration" value="{current_test.get('duration', 30) if current_test else 30}">
                    </div>
                    <div style="flex:1;">
                        <label>Tổng điểm</label>
                        <input type="number" name="totalScore" value="{current_test.get('totalScore', 100) if current_test else 100}">
                    </div>
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
            div.innerHTML = `<div style="font-weight:bold; font-size:13px; margin-bottom:8px;">Câu hỏi</div>
            <textarea name="q_content[]" placeholder="Nội dung câu hỏi..." required style="margin-bottom:8px; width:100%;" rows="3">${{content}}</textarea>
            <button type="button" onclick="this.parentElement.remove()" style="background:#ef4444; width:auto; padding:4px 10px; font-size:11px; margin-top:5px;">Xóa</button>`;
            container.appendChild(div);
        }}
        
        window.onload = function() {{
            if (existingQuestions.length > 0) {{ 
                existingQuestions.forEach(q => {{ 
                    // Escape ký tự đặc biệt để tránh lỗi JS
                    var safeContent = q.content.replace(/&/g, "&amp;")
                                               .replace(/</g, "&lt;")
                                               .replace(/>/g, "&gt;")
                                               .replace(/"/g, "&quot;")
                                               .replace(/'/g, "&#039;");
                    addQuestionInput(safeContent); 
                }}); 
            }}
            else if (document.getElementById("chkTest").checked) {{ 
                addQuestionInput(); 
            }}
        }};
    </script>
    """
    
    resp = make_response(wrap_layout(html))
    resp.set_cookie("csrf_token", csrf_token, httponly=True, samesite="Lax", secure=request.is_secure)
    return resp

@company_view_bp.route('/company/applications')
def company_applications():
    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]   
    content = "<h2>📥 Danh sách hồ sơ ứng tuyển</h2>"

    try:
        # 1. Lấy thông tin Company
        company = db_session.query(Company).filter(Company.userId == user_id).first()
        if not company:
             return wrap_layout("<h2>⚠️ Chưa có hồ sơ công ty</h2>")

        # 2. TRUY VẤN AN TOÀN (Safe Query)
        # Thay vì query cả object Application (gây lỗi Enum), ta chỉ lấy các cột cần thiết
        # và ép kiểu status sang String để tránh crash.
        apps_data = db_session.query(
            Application.id.label("app_id"),
            Application.appliedAt,
            cast(Application.status, String).label("status_safe"), # <--- FIX QUAN TRỌNG
            Student.fullName.label("student_name"),
            Job.title.label("job_title"),
            Application.jobId,
            Application.studentId
        )\
        .join(Job, Application.jobId == Job.id)\
        .join(Student, Application.studentId == Student.id)\
        .filter(Job.companyId == company.id)\
        .order_by(Application.appliedAt.desc())\
        .all()

        if not apps_data:
            content += "<p style='color:#666;'>Chưa có hồ sơ nào.</p>"
        else:
            content += """
            <table style="width:100%; border-collapse:collapse; background:white; margin-top:20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-radius:8px; overflow:hidden;">
                <thead style="background:#f1f5f9; border-bottom:2px solid #e2e8f0;">
                    <tr>
                        <th style="padding:15px; text-align:left;">Ứng viên</th>
                        <th style="padding:15px; text-align:left;">Vị trí</th>
                        <th style="padding:15px;">Điểm Test</th>
                        <th style="padding:15px;">Trạng thái</th>
                        <th style="padding:15px; text-align:right;">Hành động</th>
                    </tr>
                </thead>
                <tbody>
            """

            for row in apps_data:
                # Logic hiển thị điểm
                score_display = "--"
                test = db_session.query(SkillTest).filter(SkillTest.jobId == row.jobId).first()
                if test:
                    result = db_session.query(TestResult).filter(
                        TestResult.testId == test.id, 
                        TestResult.studentId == row.studentId
                    ).first()
                    if result:
                        score_display = f"<b>{result.score}/{test.totalScore}</b>"

                # Logic hiển thị trạng thái (Xử lý cả chữ hoa và thường)
                status_raw = str(row.status_safe).lower() # Chuyển hết về thường để so sánh
                status_html = f'<span style="font-weight:bold;">{status_raw.upper()}</span>'
                
                if "pending" in status_raw: status_html = "<span style='color:#f59e0b'>⏳ Chờ duyệt</span>"
                elif "testing" in status_raw: status_html = "<span style='color:#8b5cf6'>📝 Đang làm bài</span>"
                elif "interview" in status_raw: status_html = "<span style='color:#3b82f6'>🎤 Phỏng vấn</span>"
                elif "offered" in status_raw: status_html = "<span style='color:#16a34a'>✅ Đã Offer</span>"
                elif "rejected" in status_raw: status_html = "<span style='color:#ef4444'>❌ Từ chối</span>"

                content += f"""
                <tr style="border-bottom:1px solid #eee;">
                    <td style="padding:15px;">
                        <b>{escape(row.student_name)}</b>
                    </td>
                    <td style="padding:15px;">
                        {escape(row.job_title)}
                    </td>
                    <td style="padding:15px; text-align:center;">
                        {score_display}
                    </td>
                    <td style="padding:15px; text-align:center;">
                        <span style="background:#f8fafc; padding:4px 10px; border-radius:15px; font-size:13px; border:1px solid #e2e8f0;">
                            {status_html}
                        </span>
                    </td>
                    <td style="padding:15px; text-align:right;">
                        <a href="/company/applications/{row.app_id}/cv"
                           style="margin-right:5px; background:#2563eb; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-size:13px;">
                            <i class="fa-solid fa-eye"></i> Xem CV
                        </a>
                        <a href="/company/applications/{row.app_id}/evaluate"
                           style="background:#0f172a; color:white; padding:6px 12px; border-radius:4px; text-decoration:none; font-size:13px;">
                            <i class="fa-solid fa-pen-to-square"></i> Đánh giá
                        </a>
                    </td>
                </tr>
                """
            content += "</tbody></table>"

    except Exception as e:
        print(f"Error loading applications: {e}")
        return wrap_layout(f"<h3 style='color:red'>Lỗi tải dữ liệu: {str(e)}</h3>")

    resp = make_response(wrap_layout(content))
    return resp


@company_view_bp.route('/company/applications/<int:app_id>/evaluate', methods=['GET', 'POST'])
def company_evaluate_application(app_id):
    # 1. Kiểm tra User & CSRF
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_hex(16)

    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            return wrap_layout("<h3 style='color:red'>❌ CSRF token không hợp lệ</h3>")

    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]

    try:
        # 2. Lấy thông tin Company
        company = db_session.query(Company).filter(Company.userId == user_id).first()
        if not company:
            return wrap_layout("<h2>❌ Lỗi: Không tìm thấy thông tin công ty</h2>")

        # 3. TRUY VẤN: Lấy Application (Join để lấy Job, Student, SkillTest)
        app_item = db_session.query(Application)\
            .join(Job, Application.jobId == Job.id)\
            .filter(Application.id == app_id, Job.companyId == company.id)\
            .first()

        if not app_item:
            return wrap_layout("<h2>⛔ Bạn không có quyền truy cập hồ sơ này</h2>")

        # --- XỬ LÝ TRẠNG THÁI HIỂN THỊ ---
        status_raw = str(app_item.status) 
        if "." in status_raw:
            status = status_raw.split(".")[-1].lower() 
        else:
            status = status_raw.lower()

        # 4. XỬ LÝ POST (Lưu đánh giá)
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'interview':
                # Lưu đánh giá
                eval_obj = Evaluation(
                    applicationId=app_item.id,
                    skillScore=int(request.form.get("starRating") or 0),
                    peerReview=request.form.get("peerReview"),
                    improvement=request.form.get("improvement")
                )
                db_session.add(eval_obj)
                
                # Cập nhật trạng thái (Dùng Enum Object)
                app_item.status = ApplicationStatus.INTERVIEW 
                
                # Tạo lịch phỏng vấn
                time_str = request.form.get("interviewTime")
                interview_time = None
                if time_str:
                    try:
                        interview_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M")
                    except ValueError:
                        pass
                
                interview = Interview(
                    applicationId=app_item.id,
                    interviewDate=interview_time,
                    location=request.form.get("interviewLocation"),
                    note=request.form.get("interviewNote"),
                    status="Scheduled"
                )
                db_session.add(interview)
                
                # Thông báo (gửi đủ thời gian + địa điểm + ghi chú)
                location = (request.form.get("interviewLocation") or "").strip()
                note = (request.form.get("interviewNote") or "").strip()

                # Ưu tiên format theo datetime đã parse (đẹp hơn), fallback theo time_str
                if interview_time:
                    display_time = interview_time.strftime("%d/%m/%Y %H:%M")
                else:
                    display_time = time_str.replace("T", " ") if time_str else "Sẽ thông báo sau"

                loc_display = location if location else "Sẽ thông báo sau"

                msg = (
                    f"🎉 Chúc mừng! Bạn được mời phỏng vấn vị trí '{app_item.job.title}'. "
                    f"⏰ {display_time}. 📍 {loc_display}"
                )
                if note:
                    msg += f". 📝 {note}"

                db_session.add(Notification(userId=app_item.student.userId, content=msg))

                db_session.add(Notification(userId=app_item.student.userId, content=msg))

            elif action == 'rejected':
                app_item.status = ApplicationStatus.REJECTED 
                db_session.add(Notification(userId=app_item.student.userId, content=f"⚠️ Hồ sơ vị trí '{app_item.job.title}' của bạn chưa phù hợp lúc này."))
            
            elif action == 'offered':
                interview = db_session.query(Interview).filter(Interview.applicationId == app_item.id).order_by(Interview.id.desc()).first()
                if interview:
                    db_session.add(InterviewFeedback(
                        interviewId=interview.id,
                        feedback=request.form.get("interviewFeedback"),
                        rating=int(request.form.get("interviewRating") or 0)
                    ))
                    interview.status = "Completed"
                
                app_item.status = ApplicationStatus.OFFERED
                db_session.add(Notification(userId=app_item.student.userId, content=f"💌 CHÚC MỪNG! Bạn nhận được OFFER chính thức cho vị trí '{app_item.job.title}'."))

            db_session.commit()
            return redirect('/company/applications')

        # 5. XỬ LÝ GET (Hiển thị)
        test_details_html = ""
        if app_item.job.skill_tests:
            test = app_item.job.skill_tests[0]
            result = db_session.query(TestResult).filter(TestResult.testId == test.id, TestResult.studentId == app_item.studentId).first()
            if result:
                questions = db_session.query(Question).filter(Question.testId == test.id).all()
                student_answers = {}
                try:
                    if result.answers: student_answers = json.loads(result.answers)
                except: pass

                qa_html = ""
                for i, q in enumerate(questions, 1):
                    ans_key = f"answer_{q.id}"
                    user_ans = student_answers.get(ans_key, "<span style='color:#999'>Chưa trả lời</span>")
                    qa_html += f"""
                    <div style="margin-bottom:15px; border-bottom:1px dashed #e2e8f0; padding-bottom:10px;">
                        <p style="margin:0; font-weight:bold; color:#1e293b;">Câu {i}: {escape(q.content)}</p>
                        <div style="margin-top:5px; background:#f8fafc; padding:8px; border-radius:4px; border-left:3px solid #3b82f6;">
                            <span style="font-weight:bold; color:#3b82f6;">Trả lời:</span> {escape(user_ans)}
                        </div>
                    </div>"""
                
                test_details_html = f"""
                <div class='job-card' style='border-left:6px solid #f59e0b;'>
                    <h3>📝 Bài làm chi tiết</h3>
                    <p><b>Tổng điểm:</b> <span style="font-size:18px; color:#d97706; font-weight:bold;">{result.score} / {test.totalScore}</span></p>
                    <div style="max-height:400px; overflow-y:auto; padding-right:10px; border:1px solid #e2e8f0; padding:15px; border-radius:8px;">{qa_html}</div>
                </div>"""
            else:
                 test_details_html = "<div class='job-card'>⚠️ Ứng viên chưa làm bài test.</div>"

        form_html = ""
        if status in ['pending', 'testing']:
            form_html = f"""
            <div class="job-card" style="border-left:6px solid #8b5cf6;">
                <h3>🔍 Đánh giá năng lực & Mời phỏng vấn</h3>
                <form method="post">
                    <input type="hidden" name="csrf_token" value="{csrf_token}">
                    <div style="display:flex; gap:20px; margin-bottom:15px;">
                        <div style="flex:1;">
                            <label>Đánh giá hồ sơ (Sao)</label>
                            <select name="starRating" style="font-size:16px; color:#d97706; font-weight:bold;">
                                <option value="5">⭐⭐⭐⭐⭐ (Xuất sắc)</option>
                                <option value="4">⭐⭐⭐⭐ (Tốt)</option>
                                <option value="3" selected>⭐⭐⭐ (Khá)</option>
                                <option value="2">⭐⭐ (Trung bình)</option>
                                <option value="1">⭐ (Kém)</option>
                            </select>
                        </div>
                    </div>
                    <label>Nhận xét ưu điểm</label>
                    <textarea name="peerReview" rows="2" placeholder="Ví dụ: Tư duy logic tốt..."></textarea>
                    <div style="background:#f0fdf4; padding:20px; border-radius:8px; margin: 20px 0; border:1px solid #bbf7d0;">
                        <h4 style="margin:0 0 15px 0; color:#166534;"><i class="fa-solid fa-calendar-check"></i> Thông tin phỏng vấn</h4>
                        <div style="display:flex; gap:15px; margin-bottom:10px;">
                            <div style="flex:1;"><label style="font-size:13px;">Thời gian bắt đầu</label><input type="datetime-local" name="interviewTime" required></div>
                            <div style="flex:2;"><label style="font-size:13px;">Địa điểm / Link Online</label><input name="interviewLocation" required placeholder="VD: Phòng 202..."></div>
                        </div>
                        <label style="font-size:13px;">Ghi chú thêm</label><input name="interviewNote" placeholder="VD: Mang theo laptop...">
                    </div>
                    <div style="display:flex; gap:10px; border-top:1px solid #eee; padding-top:20px;">
                        <button name="action" value="interview" style="background:#2563eb; flex:1;">✅ Duyệt & Gửi lời mời</button>
                        <button name="action" value="rejected" style="background:#ef4444; width:auto;">❌ Từ chối</button>
                    </div>
                </form>
            </div>"""
        elif status == 'interview':
            form_html = f"""
            <div class="job-card" style="border-left:6px solid #ec4899;">
                <h3>🎤 Kết quả phỏng vấn</h3>
                <form method="post">
                    <input type="hidden" name="csrf_token" value="{csrf_token}">
                    <label>Nhận xét buổi phỏng vấn</label><textarea name="interviewFeedback" rows="5" required></textarea>
                    <label>Đánh giá chung</label>
                    <select name="interviewRating" style="font-size:16px;">
                        <option value="5">⭐⭐⭐⭐⭐ (Xuất sắc)</option>
                        <option value="4">⭐⭐⭐⭐ (Tốt)</option>
                        <option value="3">⭐⭐⭐ (Khá)</option>
                        <option value="2">⭐⭐ (Thấp)</option>
                        <option value="1">⭐ (Rất thấp)</option>
                    </select>
                    <div style="display:flex; gap:10px; margin-top:20px;">
                        <button name="action" value="offered" style="background:#16a34a; flex:1;">💌 Gửi Offer</button>
                        <button name="action" value="rejected" style="background:#ef4444; width:auto;">❌ Từ chối</button>
                    </div>
                </form>
            </div>"""
        else:
            color = "#16a34a" if status == 'offered' else "#ef4444"
            status_text = "ĐÃ TRÚNG TUYỂN" if status == 'offered' else "ĐÃ TỪ CHỐI"
            form_html = f"<div class='job-card' style='border-left: 6px solid {color}; text-align:center; padding:40px;'><h3 style='color:{color};'>{status_text}</h3><a href='/company/applications'>Quay lại</a></div>"

        html = f"<h2>⚖️ Quy trình tuyển dụng: {escape(app_item.student.fullName)}</h2>{test_details_html}{form_html}"

        resp = make_response(wrap_layout(html))
        
        # --- FIX: Set cookie để CSRF hoạt động ---
        resp.set_cookie(
            "csrf_token",
            csrf_token,
            httponly=True,
            samesite="Lax",
            secure=request.is_secure
        )
        return resp

    except Exception as e:
        db_session.rollback()
        print(f"Error evaluating app: {e}")
        return wrap_layout(f"<h3>❌ Lỗi hệ thống: {str(e)}</h3>")
    

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
    # 1. Kiểm tra đăng nhập
    user = require_company_view()
    if not user:
        return redirect('/login')

    user_id = user["id"]

    try:
        # 2. Lấy Company hiện tại
        company = db_session.query(Company).filter(Company.userId == user_id).first()
        if not company:
            return wrap_layout("<h2>❌ Lỗi: Không tìm thấy thông tin công ty</h2>")

        # 3. TRUY VẤN TRỰC TIẾP: Lấy Application và kiểm tra quyền sở hữu
        # Logic: Tìm Application có ID = app_id VÀ thuộc Job của Company này
        app_item = db_session.query(Application)\
            .join(Job, Application.jobId == Job.id)\
            .filter(Application.id == app_id, Job.companyId == company.id)\
            .first()

        # Nếu không tìm thấy -> Tức là hồ sơ không tồn tại hoặc không thuộc công ty này
        if not app_item:
            return wrap_layout("<h2>⛔ Bạn không có quyền truy cập hồ sơ này</h2>")

        # 4. Lấy dữ liệu Student & Profile
        student = app_item.student
        profile = student.profile
        
        # Xử lý Skills (danh sách kỹ năng)
        skills_html = ""
        if student.skills:
            for s in student.skills:
                # Kiểm tra null safe cho skill name
                skill_name = s.skill.name if s.skill else "Unknown"
                skills_html += f'<span class="badge-skill">{skill_name} (Lv.{s.level})</span>'
        
        if not skills_html:
            skills_html = '<span style="color:#999; font-style:italic;">Chưa cập nhật kỹ năng.</span>'

        # Xử lý các trường dữ liệu có thể null
        dob = student.dob.strftime("%d/%m/%Y") if student.dob else "Chưa cập nhật"
        cccd = getattr(student, "cccd", "Chưa cập nhật") or "Chưa cập nhật"
        
        edu_level = profile.educationLevel if profile else "Chưa cập nhật"
        degrees = profile.degrees if profile else "Chưa cập nhật"
        about = profile.about if profile else "Ứng viên chưa viết giới thiệu."
        cv_url = profile.cvUrl if profile else "#"
        portfolio_url = getattr(profile, "portfolioUrl", None)

        # 5. Render Giao diện (HTML)
        content = f"""
        <h2>📄 Chi tiết hồ sơ ứng viên</h2>
        <a href="/company/applications">← Quay lại danh sách</a>

        <div class="job-card">
            <div class="cv-container">
                <div class="cv-left">
                    <img src="https://ui-avatars.com/api/?name={escape(student.fullName)}&size=128&background=random&color=fff&rounded=true" 
                         style="border-radius:50%; margin-bottom:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" alt="Avatar">
                    
                    <h2 style="color:#1e40af; margin-bottom:5px;">{escape(student.fullName)}</h2>
                    <p style="color:#64748b; font-weight:bold; margin-top:0;">{escape(student.major or 'Chưa có ngành')}</p>
                    
                    <hr style="border:0; border-top:1px solid #e2e8f0; margin: 20px 0;">
                    
                    <p style="font-size:13px; color:#64748b;">Vị trí ứng tuyển</p>
                    <p style="font-weight:bold; color:#0f172a;">{escape(app_item.job.title)}</p>
                    
                    <div style="margin-top:30px;">
                        <a href="{cv_url}" target="_blank">
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
                        <div style="flex:1;"><strong>🆔 CCCD:</strong> {escape(cccd)}</div>
                    </div>

                    <div class="section-title"><i class="fa-solid fa-graduation-cap"></i> Học vấn & Bằng cấp</div>
                    <p><strong>🎓 Trình độ:</strong> {escape(edu_level)}</p>
                    <p><strong>📜 Chứng chỉ:</strong> {escape(degrees)}</p>

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

    except Exception as e:
        print(f"Error viewing CV: {e}")
        return wrap_layout(f"<h3>❌ Lỗi hệ thống: {str(e)}</h3>")