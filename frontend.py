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
        user_role = st.session_state.user.get('role', 'student').lower()
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
    role_choice = st.selectbox("Bạn là ai?", ["Sinh viên (Student)", "Nhà tuyển dụng (Company)"]) # Admin thường tạo cứng trong DB
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
                    st.success("✅ Đăng ký thành công! Vui lòng đăng nhập.")
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
                # Demo: Lấy tất cả user check (Thực tế nên có API /login trả về token)
                res = requests.get(f"{API_URL}/users/")
                if res.status_code == 200:
                    users = res.json()
                    user = next((u for u in users if u['email'] == email), None) # Bỏ qua check pass cho demo
                    if user:
                        st.session_state.is_logged_in = True
                        st.session_state.user = user
                        st.success(f"Chào mừng {user.get('role')}!")
                        st.rerun()
                    else:
                        st.error("Sai email hoặc mật khẩu.")
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")

# ================= MODULE: STUDENT =================
elif choice == "📄 Hồ sơ & Kỹ năng":
    st.header("👤 Hồ sơ cá nhân & Kỹ năng")
    user_id = st.session_state.user['id']
    
    # 1. Thông tin cơ bản
    try:
        res = requests.get(f"{API_URL}/students/user/{user_id}")
        student_data = res.json() if res.status_code == 200 else {}
    except: student_data = {}

    with st.expander("Thông tin cơ bản", expanded=True):
        with st.form("update_profile"):
            fn = st.text_input("Họ tên", value=student_data.get("fullName", ""))
            mj = st.text_input("Chuyên ngành", value=student_data.get("major", ""))
            if st.form_submit_button("Lưu thông tin"):
                # TODO: Gọi API PUT update profile
                st.success("Đã lưu thông tin cơ bản!")

    # 2. Kỹ năng & Trình độ (Để Matching)
    st.subheader("🛠 Kỹ năng của bạn")
    st.info("Cập nhật kỹ năng để hệ thống gợi ý việc làm phù hợp.")
    
    col1, col2 = st.columns(2)
    with col1:
        my_skills = st.multiselect("Chọn kỹ năng bạn có:", 
                                   ["Python", "Java", "ReactJS", "SQL", "Communication", "English"],
                                   default=["Python"]) # Demo default
    with col2:
        level = st.selectbox("Trình độ hiện tại:", ["Fresher", "Junior", "Senior", "Intern"])
    
    if st.button("Cập nhật Kỹ năng"):
        # TODO: Gọi API lưu skill vào bảng student_skills
        st.success(f"Đã lưu bộ kỹ năng: {', '.join(my_skills)} - Level: {level}")

elif choice == "🏠 Việc làm & Matching":
    st.header("Tìm kiếm việc làm")
    
    # Giả lập Matching: Lấy skill của user so với skill của Job
    user_skills = {"Python", "SQL"} # Giả sử lấy từ DB
    
    try:
        jobs = requests.get(f"{API_URL}/jobs/").json()
        
        col_search, col_filter = st.columns([3, 1])
        search_term = col_search.text_input("Tìm kiếm theo từ khóa...")
        
        for job in jobs:
            # Giả lập skill của job
            job_req_skills = set(job.get('skills', ["Python", "Java"])) # Demo data
            match_score = len(user_skills.intersection(job_req_skills))
            is_match = match_score > 0
            
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <div style="display:flex; justify-content:space-between;">
                        <h3>{job['title']}</h3>
                        {'<span class="match-badge">⚡ PHÙ HỢP VỚI BẠN</span>' if is_match else ''}
                    </div>
                    <p>🏢 {job.get('companyName', 'Mã cty: ' + str(job['companyId']))} | 📍 {job.get('location', 'N/A')}</p>
                    <p style="font-size:0.9em; color:#666;">Yêu cầu: {', '.join(list(job_req_skills))}</p>
                    <hr>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([1, 5])
                if c1.button("Ứng tuyển", key=f"apply_{job['id']}"):
                    # TODO: Check limit, gọi API apply
                    st.success("Đã nộp đơn thành công!")

    except Exception as e:
        st.error(f"Lỗi tải danh sách việc làm: {e}")

elif choice == "📝 Làm bài Test Kỹ năng":
    st.header("📝 Bài kiểm tra năng lực")
    st.caption("Hoàn thành các bài test để tăng độ uy tín với nhà tuyển dụng.")
    
    # Demo danh sách bài test
    tests = [
        {"id": 1, "name": "Python Basic", "company": "FPT Software", "duration": "15 mins"},
        {"id": 2, "name": "IQ Test", "company": "VNG", "duration": "30 mins"}
    ]
    
    for t in tests:
        with st.expander(f"{t['name']} - {t['company']}"):
            st.write(f"Thời gian: {t['duration']}")
            if st.button(f"Làm bài ngay", key=f"take_test_{t['id']}"):
                st.session_state.current_test = t
                st.info("Đang chuyển hướng vào bài làm... (Chức năng Demo)")

elif choice == "✅ Ứng tuyển của tôi":
    st.header("Lịch sử ứng tuyển")
    # Giữ nguyên logic cũ, có thể bổ sung hiển thị kết quả bài test nếu có
    st.write("Danh sách các công việc đã nộp hồ sơ...")

# ================= MODULE: COMPANY =================
elif choice == "🏢 Đăng Tin & Skill":
    st.header("Đăng tin tuyển dụng mới")
    
    with st.form("post_job"):
        title = st.text_input("Tiêu đề")
        location = st.text_input("Địa điểm")
        # Chức năng thêm: Giới hạn số lượng
        limit = st.number_input("Giới hạn số lượng hồ sơ nhận", min_value=1, value=50)
        # Chức năng thêm: Chọn Skill yêu cầu (Tagging)
        req_skills = st.multiselect("Kỹ năng yêu cầu (Job Skill)", ["Python", "Java", "C++", "Office", "English"])
        desc = st.text_area("Mô tả công việc")
        
        if st.form_submit_button("Đăng tin"):
            # Payload thêm fields: limit, skills
            st.success(f"Đã đăng tin '{title}' với giới hạn {limit} hồ sơ.")

elif choice == "📋 Quản lý Tin & Ứng viên":
    st.header("Quản lý tuyển dụng")
    user_id = st.session_state.user['id']
    
    # 1. Danh sách Job đã đăng
    st.subheader("Danh sách Tin đăng")
    # Mock data job của cty
    my_jobs = [{"id": 101, "title": "Backend Dev", "applicants": 5, "status": "open"}]
    
    for job in my_jobs:
        with st.expander(f"{job['title']} (Đang có {job['applicants']} ứng viên)"):
            c1, c2, c3 = st.columns(3)
            c1.button("Sửa tin", key=f"edit_{job['id']}")
            if c2.button("❌ Xóa tin", key=f"del_{job['id']}"):
                st.warning("Đã gửi lệnh xóa tin.")
            if c3.button("🔒 Đóng đơn", key=f"close_{job['id']}"):
                st.info("Đã ngừng nhận hồ sơ.")
            
            st.divider()
            st.write("👨‍🎓 **Danh sách ứng viên:**")
            
            # Kết nối thông tin Student: Hiển thị list ứng viên
            # Mock applicants
            applicants = [
                {"name": "Nguyễn Văn A", "major": "KTPM", "score": "8.5"},
                {"name": "Trần Thị B", "major": "HTTT", "score": "7.0"}
            ]
            
            df = pd.DataFrame(applicants)
            st.table(df)
            st.caption("Nhấn vào tên ứng viên để xem chi tiết Profile (Tính năng nâng cao).")

elif choice == "🧩 Tạo bài Test":
    st.header("Thiết lập bài Test Kỹ năng")
    st.info("Tạo câu hỏi sàng lọc cho ứng viên trước khi nộp hồ sơ.")
    
    job_target = st.selectbox("Áp dụng cho Job nào?", ["Backend Dev", "Data Analyst"])
    
    with st.form("create_test"):
        q_name = st.text_input("Tên bài test")
        question = st.text_area("Nội dung câu hỏi (Hoặc link Google Form)")
        time_limit = st.slider("Giới hạn thời gian (phút)", 5, 60, 15)
        
        if st.form_submit_button("Tạo bài test"):
            st.success(f"Đã tạo bài test cho job {job_target}")

elif choice == "🏢 Hồ sơ Công ty":
    # Logic cũ: Tạo/Sửa profile công ty
    st.header("Cập nhật thông tin doanh nghiệp")
    st.text_input("Tên công ty")
    st.text_input("Website")
    st.button("Lưu")

# ================= MODULE: ADMIN =================
elif choice == "📢 Quản lý Thông báo":
    st.header("📢 Tạo Thông báo Hệ thống")
    st.info("Tin nhắn này sẽ hiện lên trang chủ của tất cả user.")
    
    with st.form("admin_announce"):
        title = st.text_input("Tiêu đề thông báo")
        content = st.text_area("Nội dung")
        audience = st.selectbox("Gửi tới:", ["Tất cả", "Chỉ Sinh viên", "Chỉ Doanh nghiệp"])
        
        if st.form_submit_button("Phát thông báo"):
            # TODO: POST /announcements/
            st.success("Đã gửi thông báo thành công!")

    st.subheader("Lịch sử thông báo")
    st.write("Chưa có thông báo nào.")

elif choice == "🛡 Xem Báo cáo (Reports)":
    st.header("🛡 Xử lý Vi phạm & Báo cáo")
    
    # Tab phân loại report
    tab1, tab2 = st.tabs(["Báo cáo từ SV", "Báo cáo từ Cty"])
    
    with tab1:
        st.write("Danh sách SV báo cáo tin tuyển dụng lừa đảo:")
        # Mock data
        st.error("Report #12: Cty X yêu cầu đóng tiền (User: bao123)")
        if st.button("Xử lý", key="r1"): st.write("Đã đánh dấu đã xem.")
        
    with tab2:
        st.write("Danh sách Cty báo cáo ứng viên spam:")
        st.info("Hiện chưa có báo cáo nào.")

elif choice == "👥 Quản lý Users":
    st.header("Quản lý người dùng")
    st.write("Danh sách toàn bộ user trong hệ thống (View Only).")
    try:
        users = requests.get(f"{API_URL}/users/").json()
        st.dataframe(users)
    except:
        st.warning("Không kết nối được Backend.")

# ================= MODULE: CHUNG (REPORT & GUEST) =================
elif choice == "🚩 Gửi Báo cáo (Report)":
    st.header("Gửi phản hồi / Báo cáo vi phạm")
    
    report_type = st.selectbox("Vấn đề gặp phải", ["Lỗi hệ thống", "Tin tuyển dụng ảo", "Spam", "Khác"])
    detail = st.text_area("Mô tả chi tiết")
    
    if st.button("Gửi báo cáo"):
        # TODO: POST /reports/
        st.success("Cảm ơn bạn đã phản hồi. Admin sẽ xem xét sớm nhất!")

elif choice == "👀 Xem Job (Khách)":
    st.header("Cơ hội việc làm (Chế độ Khách)")
    st.warning("Bạn đang xem với tư cách Khách. Vui lòng Đăng nhập để Ứng tuyển.")
    
    # Logic hiển thị Job cho khách (đã fix hiển thị tên cty)
    try:
        jobs = requests.get(f"{API_URL}/jobs/").json()
        for job in jobs:
            st.markdown(f"""
            <div class="job-card">
                <h3>{job['title']}</h3>
                <p>🏢 {job.get('companyName', 'Công ty Ẩn danh')} | 📍 {job.get('location')}</p>
                <hr>
                <p>{job.get('description')}</p>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.error("Chưa có dữ liệu.")