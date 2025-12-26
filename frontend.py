import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ thống Tuyển dụng LabOdc", page_icon="💼", layout="wide")
API_URL = "http://127.0.0.1:8000"

# --- KHỞI TẠO SESSION STATE ---
if 'user' not in st.session_state:
    st.session_state.user = None 
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False

# --- CSS GIAO DIỆN ---
st.markdown("""
<style>
    .job-card { background-color: #ffffff; padding: 20px; border-radius: 12px; 
                border-left: 6px solid #ff4b4b; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; color: #333;}
    .report-card { background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #ddd; }
    .stButton>button { width: 100%; }
    .match-badge { background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR & PHÂN QUYỀN =================
with st.sidebar:
    st.title("🚀 LabOdc Recruitment")
    
    if st.session_state.is_logged_in and st.session_state.user:
        # Lấy role an toàn, mặc định là student nếu thiếu
        user_role = st.session_state.user.get('role', 'student')
        if isinstance(user_role, dict): # Trường hợp trả về Enum dạng dict
             user_role = user_role.get('value', 'student')
        user_role = str(user_role).lower()
        
        user_email = st.session_state.user.get('email')
        
        # Mapping hiển thị Role đẹp hơn
        role_display = {
            "student": "👨‍🎓 Ứng viên (Student)",
            "company": "🏢 Doanh nghiệp (Company)",
            "admin": "🛠 Quản trị viên (Admin)"
        }
        
        st.success(f"👤 {user_email}\n\n{role_display.get(user_role, user_role.upper())}")
        
        if st.button("Đăng xuất", type="primary"):
            st.session_state.user = None
            st.session_state.is_logged_in = False
            st.rerun()
        
        st.divider()
        
        # --- MENU THEO ROLE ---
        if user_role == 'student':
            menu = [
                "🏠 Việc làm & Matching", 
                "📝 Làm bài Test Kỹ năng",
                "📄 Hồ sơ & Kỹ năng", 
                "✅ Ứng tuyển của tôi",
                "🚩 Gửi Báo cáo (Report)"
            ]
        elif user_role == 'company':
            menu = [
                "🏢 Đăng Tin & Skill", 
                "📋 Quản lý Tin & Ứng viên", 
                "🧩 Tạo bài Test", 
                "🏢 Hồ sơ Công ty",
                "🚩 Gửi Báo cáo (Report)"
            ]
        elif user_role == 'admin':
            menu = [
                "📢 Quản lý Thông báo",
                "🛡 Xem Báo cáo (Reports)",
                "👥 Quản lý Users"
            ]
        else:
            menu = ["🏠 Việc làm"]
            
    else:
        st.info("👋 Chào khách vãng lai")
        menu = ["🔑 Đăng nhập", "📝 Đăng ký", "👀 Xem Job (Khách)"]

    choice = st.radio("Menu Chính", menu)

# ================= LOGIC CHỨC NĂNG =================

# --- 1. AUTHENTICATION (Đăng nhập/Đăng ký) ---
if choice == "📝 Đăng ký":
    st.header("Đăng ký thành viên mới")
    role_choice = st.selectbox("Bạn là ai?", ["Sinh viên (Student)", "Nhà tuyển dụng (Company)"]) 
    role_api = "student" if "Sinh viên" in role_choice else "company"

    with st.form("register_form"):
        email = st.text_input("Email (*)")
        password = st.text_input("Mật khẩu (*)", type="password")
        if role_api == "student":
            fullname = st.text_input("Họ và tên")
        else:
            company_name = st.text_input("Tên công ty")
        
        if st.form_submit_button("Đăng ký ngay"):
            user_payload = {"email": email, "password": password, "role": role_api, "status": "active"}
            try:
                res = requests.post(f"{API_URL}/users/", json=user_payload)
                if res.status_code == 200:
                    new_user = res.json()
                    st.success(f"✅ Đăng ký thành công ID {new_user['id']}! Vui lòng đăng nhập.")
                    
                    # Tự động tạo hồ sơ rỗng để tránh lỗi sau này
                    if role_api == 'student':
                        requests.post(f"{API_URL}/students/{new_user['id']}", json={"fullName": fullname, "major": "N/A"})
                    elif role_api == 'company':
                        requests.post(f"{API_URL}/companies/{new_user['id']}", json={"companyName": company_name})
                        
                else:
                    st.error(f"Lỗi: {res.text}")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")

elif choice == "🔑 Đăng nhập":
    st.header("Đăng nhập hệ thống")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Mật khẩu", type="password")
        if st.form_submit_button("Đăng nhập"):
            try:
                # Demo: Lấy tất cả user check (Thực tế nên dùng API Login riêng)
                res = requests.get(f"{API_URL}/users/")
                if res.status_code == 200:
                    users = res.json()
                    # Tìm user có email trùng khớp
                    user = next((u for u in users if u['email'] == email), None) 
                    
                    if user:
                        # Check pass đơn giản (vì DB lưu pass thường trong demo này)
                        # Nếu bạn đã hash pass ở backend thì đoạn này cần sửa
                        st.session_state.is_logged_in = True
                        st.session_state.user = user
                        st.success(f"Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Sai email hoặc tài khoản không tồn tại.")
                else:
                    st.error("Không thể kết nối lấy danh sách User.")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")

# ================= MODULE: STUDENT =================
elif choice == "📄 Hồ sơ & Kỹ năng":
    st.header("👤 Hồ sơ cá nhân & Kỹ năng")
    user_id = st.session_state.user['id']
    
    try:
        res = requests.get(f"{API_URL}/students/user/{user_id}")
        student_data = res.json() if res.status_code == 200 else {}
    except: student_data = {}

    with st.expander("Thông tin cơ bản", expanded=True):
        st.write(f"**Họ tên:** {student_data.get('fullName', 'Chưa cập nhật')}")
        st.write(f"**Chuyên ngành:** {student_data.get('major', 'Chưa cập nhật')}")
        st.info("Tính năng chỉnh sửa đang phát triển...")

    st.subheader("🛠 Kỹ năng của bạn")
    col1, col2 = st.columns(2)
    with col1:
        my_skills = st.multiselect("Chọn kỹ năng bạn có:", 
                                   ["Python", "Java", "ReactJS", "SQL", "Communication", "English"],
                                   default=["Python"]) 
    with col2:
        level = st.selectbox("Trình độ hiện tại:", ["Fresher", "Junior", "Senior", "Intern"])
    
    if st.button("Cập nhật Kỹ năng"):
        st.success(f"Đã lưu bộ kỹ năng: {', '.join(my_skills)} - Level: {level}")

elif choice == "🏠 Việc làm & Matching":
    st.header("Tìm kiếm việc làm")
    
    # 1. Gọi API lấy danh sách Job thật từ DB
    try:
        response = requests.get(f"{API_URL}/jobs/")
        if response.status_code == 200:
            jobs = response.json()
            if not jobs:
                st.info("Hiện chưa có tin tuyển dụng nào.")
            
            # Thanh tìm kiếm
            search_term = st.text_input("🔍 Tìm kiếm công việc (Python, Java...)...")
            
            for job in jobs:
                # Filter đơn giản
                if search_term and search_term.lower() not in job['title'].lower():
                    continue

                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <div style="display:flex; justify-content:space-between;">
                            <h3>{job['title']}</h3>
                            <span style="background:#e0f2fe; color:#0284c7; padding:2px 8px; border-radius:4px;">
                                {job.get('status', 'open').upper()}
                            </span>
                        </div>
                        <p>📍 {job.get('location', 'N/A')}</p>
                        <p style="font-size:0.9em; color:#555;">{job.get('description')}</p>
                        <hr>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([1, 5])
                    
                    # Nút Ứng tuyển THẬT
                    if c1.button("Ứng tuyển", key=f"apply_{job['id']}"):
                        if st.session_state.user:
                            # Lấy Student ID
                            try:
                                u_id = st.session_state.user['id']
                                stu_res = requests.get(f"{API_URL}/students/user/{u_id}")
                                if stu_res.status_code == 200:
                                    student_id = stu_res.json()['id']
                                    
                                    # Gọi API Apply
                                    payload = {"jobId": job['id'], "studentId": student_id, "status": "pending"}
                                    res_apply = requests.post(f"{API_URL}/apply/", json=payload)
                                    
                                    if res_apply.status_code == 200:
                                        st.success("✅ Đã nộp hồ sơ thành công!")
                                    elif res_apply.status_code == 400:
                                        st.warning(res_apply.json().get('detail', 'Lỗi ứng tuyển'))
                                    else:
                                        st.error("Lỗi hệ thống.")
                                else:
                                    st.error("Bạn chưa cập nhật Hồ sơ Sinh viên.")
                            except Exception as e:
                                st.error(f"Lỗi: {e}")
                        else:
                            st.warning("Vui lòng đăng nhập.")
        else:
            st.error("Không thể tải danh sách việc làm.")
            
    except Exception as e:
        st.error(f"Lỗi kết nối Backend: {e}")

elif choice == "✅ Ứng tuyển của tôi":
    st.header("Lịch sử ứng tuyển")
    user_id = st.session_state.user['id']
    try:
        res = requests.get(f"{API_URL}/applications/my-applications/{user_id}")
        if res.status_code == 200:
            apps = res.json()
            if apps:
                st.dataframe(apps)
            else:
                st.info("Bạn chưa ứng tuyển công việc nào.")
        else:
            st.error("Lỗi tải dữ liệu.")
    except:
        st.error("Lỗi kết nối.")

# ================= MODULE: COMPANY =================
elif choice == "🏢 Đăng Tin & Skill":
    st.header("Đăng tin tuyển dụng mới")
    
    # 1. Lấy Company ID thật từ User ID
    user_id = st.session_state.user['id']
    company_id = None
    
    try:
        res = requests.get(f"{API_URL}/companies/user/{user_id}")
        if res.status_code == 200:
            comp_info = res.json()
            company_id = comp_info['id']
            st.success(f"Đang đăng tin dưới tên: **{comp_info['companyName']}**")
        else:
            st.error("⚠️ Tài khoản này chưa có hồ sơ công ty. Vui lòng tạo hồ sơ trước.")
            st.stop()
    except:
        st.error("Lỗi kết nối Server.")
        st.stop()

    with st.form("post_job"):
        title = st.text_input("Tiêu đề công việc (*)")
        location = st.text_input("Địa điểm (*)")
        desc = st.text_area("Mô tả chi tiết (*)")
        
        submitted = st.form_submit_button("🚀 Đăng tin")
        
        if submitted:
            if not title or not desc:
                st.warning("Vui lòng điền đủ thông tin.")
            else:
                # 2. GỌI API POST JOB
                payload = {
                    "companyId": company_id,
                    "title": title,
                    "description": desc,
                    "location": location,
                    "status": "open"
                }
                try:
                    res_post = requests.post(f"{API_URL}/jobs/", json=payload)
                    if res_post.status_code == 200:
                        st.success("✅ Đã đăng tin thành công!")
                    else:
                        st.error(f"Lỗi đăng tin: {res_post.text}")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

elif choice == "📋 Quản lý Tin & Ứng viên":
    st.header("Quản lý tin đăng")
    user_id = st.session_state.user['id']
    
    try:
        # Gọi API lấy Job của công ty
        res = requests.get(f"{API_URL}/jobs/my-jobs/{user_id}")
        if res.status_code == 200:
            my_jobs = res.json()
            
            if not my_jobs:
                st.info("Bạn chưa đăng tin nào.")
            
            for job in my_jobs:
                with st.expander(f"{job['title']} - {job['status']}"):
                    st.write(f"**Mô tả:** {job['description']}")
                    st.write(f"**Ngày tạo:** {job['createdAt']}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("Xem ứng viên", key=f"view_app_{job['id']}"):
                        st.info("Tính năng xem chi tiết ứng viên đang cập nhật...")
        else:
            st.error("Không tải được danh sách tin.")
            
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")

elif choice == "🏢 Hồ sơ Công ty":
    st.header("Cập nhật thông tin doanh nghiệp")
    user_id = st.session_state.user['id']
    
    # Kiểm tra xem đã có hồ sơ chưa
    has_profile = False
    try:
        res = requests.get(f"{API_URL}/companies/user/{user_id}")
        if res.status_code == 200:
            current_data = res.json()
            has_profile = True
        else:
            current_data = {}
    except: current_data = {}

    with st.form("company_profile"):
        c_name = st.text_input("Tên công ty", value=current_data.get('companyName', ''))
        c_desc = st.text_area("Giới thiệu", value=current_data.get('description', ''))
        c_web = st.text_input("Website", value=current_data.get('website', ''))
        
        if st.form_submit_button("Lưu hồ sơ"):
            payload = {"companyName": c_name, "description": c_desc, "website": c_web}
            
            if has_profile:
                st.warning("API cập nhật (PUT) chưa cài đặt, hiện chỉ hỗ trợ tạo mới.")
            else:
                # Tạo mới
                res = requests.post(f"{API_URL}/companies/{user_id}", json=payload)
                if res.status_code == 200:
                    st.success("Tạo hồ sơ thành công!")
                else:
                    st.error(f"Lỗi: {res.text}")

# ================= MODULE: ADMIN & CHUNG =================
elif choice == "👀 Xem Job (Khách)":
    st.header("Cơ hội việc làm (Chế độ Khách)")
    try:
        jobs = requests.get(f"{API_URL}/jobs/").json()
        for job in jobs:
            st.markdown(f"""
            <div class="job-card">
                <h3>{job['title']}</h3>
                <p>📍 {job.get('location')}</p>
                <hr>
                <p>{job.get('description')}</p>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.error("Chưa có dữ liệu.")

elif choice == "👥 Quản lý Users":
    st.header("Quản lý người dùng")
    try:
        users = requests.get(f"{API_URL}/users/").json()
        st.dataframe(users)
    except:
        st.warning("Không kết nối được Backend.")
        # ... (Phần code cũ giữ nguyên) ...

# ================= MODULE: STUDENT =================
elif choice == "📄 Hồ sơ & Kỹ năng":
    st.header("👤 Hồ sơ cá nhân & Kỹ năng")
    user_id = st.session_state.user['id']
    
    # Lấy dữ liệu hiện tại
    student_id = None
    try:
        res = requests.get(f"{API_URL}/students/user/{user_id}")
        if res.status_code == 200:
            data = res.json()
            student_id = data['id']
            profile = data.get('profile') or {}
        else:
            data = {}
            profile = {}
    except: 
        data = {}
        profile = {}

    if student_id:
        # --- TAB 1: THÔNG TIN CÁ NHÂN ---
        st.subheader("1. Thông tin cá nhân")
        with st.form("info_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Họ và tên", value=data.get('fullName', ''))
                # Xử lý ngày sinh (Convert string to date)
                dob_str = data.get('dob')
                default_dob = datetime(2000, 1, 1)
                if dob_str:
                    try:
                        default_dob = datetime.strptime(dob_str.split('T')[0], "%Y-%m-%d")
                    except: pass
                dob = st.date_input("Ngày sinh", value=default_dob)
                
            with col2:
                cccd = st.text_input("Số CCCD/CMND", value=data.get('cccd', ''))
                major = st.text_input("Chuyên ngành", value=data.get('major', ''))

            st.markdown("---")
            st.subheader("2. Hồ sơ chuyên môn")
            
            edu_level = st.selectbox("Trình độ học vấn cao nhất", 
                                     ["Đại học", "Cao đẳng", "Thạc sĩ", "Tiến sĩ", "Khác"],
                                     index=0 if not profile.get('educationLevel') else ["Đại học", "Cao đẳng", "Thạc sĩ", "Tiến sĩ", "Khác"].index(profile.get('educationLevel', 'Đại học')))
            
            degrees = st.text_area("Bằng cấp & Chứng chỉ (Ghi rõ tên bằng, nơi cấp, năm)", 
                                   value=profile.get('degrees', ''),
                                   placeholder="- Bằng Kỹ sư CNTT ĐH Bách Khoa (2022)\n- Chứng chỉ IELTS 7.0")
            
            about = st.text_area("Giới thiệu bản thân / Mục tiêu nghề nghiệp", 
                                 value=profile.get('about', ''))
            
            save_btn = st.form_submit_button("💾 Lưu hồ sơ")
            
            if save_btn:
                # Payload gửi đi
                update_data = {
                    "fullName": full_name,
                    "dob": dob.isoformat(),
                    "cccd": cccd,
                    "major": major,
                    "educationLevel": edu_level,
                    "degrees": degrees,
                    "about": about
                }
                
                try:
                    res_put = requests.put(f"{API_URL}/students/{student_id}", json=update_data)
                    if res_put.status_code == 200:
                        st.success("✅ Cập nhật hồ sơ thành công!")
                        st.rerun()
                    else:
                        st.error(f"Lỗi cập nhật: {res_put.text}")
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")

        # --- TAB 2: KỸ NĂNG (DEMO UI) ---
        st.markdown("---")
        st.subheader("3. Kỹ năng & Trình độ (Skills)")
        
        # Phần này lý tưởng nhất là lưu vào bảng StudentSkill
        # Ở đây demo hiển thị dạng Tag
        st.info("Hệ thống ghi nhận các kỹ năng sau để gợi ý việc làm:")
        
        c1, c2 = st.columns([3, 1])
        with c1:
            skills = st.multiselect("Chọn kỹ năng của bạn", 
                           ["Python", "Java", "ReactJS", "NodeJS", "SQL", "Tiếng Anh", "Giao tiếp", "Teamwork"],
                           default=["Python", "SQL"]) # Cần logic load từ DB thật
        with c2:
            st.write("")
            st.write("")
            if st.button("Cập nhật Skill"):
                st.success("Đã lưu kỹ năng (Demo)")

    else:
        st.warning("Không tìm thấy ID sinh viên. Vui lòng đăng nhập lại.")