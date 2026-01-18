from flask import Blueprint, request, jsonify
from database import db_session
from datetime import datetime
# Import models
from models.user_models import User, Student, Company, CompanyProfile, StudentProfile, UserRole
from models.app_models import Notification 

user_bp = Blueprint('user_router', __name__)

# =========================
# GET ALL USERS (ADMIN)
# =========================
@user_bp.route("/users/", methods=["GET"])
def get_users():
    users = db_session.query(User).all()
    return jsonify([{
        "id": u.id,
        "email": u.email,
        "role": u.role.value,
        "status": u.status,
        "createdAt": u.createdAt.isoformat()
    } for u in users])


# =========================
# CREATE USER (REGISTER) - ĐÃ FIX LỖI ENUM
# =========================
@user_bp.route("/users/", methods=["POST"])
def create_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    role_str = data.get("role", "student") # Lấy chuỗi từ frontend

    # 1. Kiểm tra email trùng
    if db_session.query(User).filter(User.email == email).first():
        return jsonify({"detail": "Email đã tồn tại"}), 400

    try:
        # --- BƯỚC QUAN TRỌNG: Chuyển chuỗi thành Enum Object ---
        # UserRole("student") sẽ trả về UserRole.STUDENT
        try:
            role_enum = UserRole(role_str)
        except ValueError:
            # Nếu gửi sai, mặc định là student
            role_enum = UserRole.STUDENT

        # 2. Tạo User (Truyền Enum Object vào)
        new_user = User(
            email=email,
            password=password, 
            role=role_enum, # <--- Đã sửa: Truyền object Enum, không truyền string
            status="active"
        )
        db_session.add(new_user)
        db_session.flush() # Để lấy new_user.id ngay lập tức

        # 3. Tạo thông tin chi tiết tùy theo Role
        # So sánh với Enum Object để chính xác
        if role_enum == UserRole.STUDENT:
            # Tạo Student
            new_student = Student(
                userId=new_user.id,
                fullName=email.split("@")[0], 
                major="Chưa cập nhật"
            )
            db_session.add(new_student)
            db_session.flush()
            
            # Tạo Profile Student mặc định
            new_profile = StudentProfile(studentId=new_student.id)
            db_session.add(new_profile)

        elif role_enum == UserRole.COMPANY:
            # Tạo Company 
            new_company = Company(
                userId=new_user.id,
                companyName=email.split("@")[0] 
            )
            db_session.add(new_company)
            db_session.flush() # Lấy ID công ty

            # Tạo Company Profile rỗng để tránh lỗi
            new_profile = CompanyProfile(
                companyId=new_company.id,
                description="",
                address="",
                website=""
            )
            db_session.add(new_profile)

        db_session.commit()
        return jsonify({
            "id": new_user.id,
            "email": new_user.email,
            "role": new_user.role.value, # Trả về value (string) cho frontend
            "message": "Đăng ký thành công"
        }), 201

    except Exception as e:
        db_session.rollback()
        print(f"Register Error: {e}") 
        return jsonify({"detail": f"Lỗi server: {str(e)}"}), 500


# =========================
# LOGIN
# =========================
@user_bp.route("/login/", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # 1. Tìm user
    user = db_session.query(User).filter(User.email == email).first()

    # 2. Nếu KHÔNG tìm thấy user
    if not user:
        return jsonify({"detail": "Sai tài khoản hoặc mật khẩu"}), 401

    # 3. Kiểm tra mật khẩu
    if user.password != password:
        return jsonify({"detail": "Sai tài khoản hoặc mật khẩu"}), 401

    # 4. Kiểm tra status an toàn
    current_status = getattr(user, "status", "active")
    if current_status != "active":
        return jsonify({"detail": "Tài khoản đã bị khóa"}), 403
            
    # 5. Đăng nhập thành công
    return jsonify({
        "id": user.id,
        "email": user.email,
        "role": user.role.value # Trả về string (vd: "student")
    }), 200

# =========================
# GET NOTIFICATIONS
# =========================
@user_bp.route("/notifications/<int:user_id>", methods=["GET"])
def get_notifications(user_id):
    """Lấy danh sách thông báo của user"""
    notifications = db_session.query(Notification).filter(
        Notification.userId == user_id
    ).order_by(Notification.createdAt.desc()).all()

    return jsonify([{
        "id": n.id,
        "content": n.content,
        "isRead": n.isRead,
        "createdAt": n.createdAt.strftime("%Y-%m-%d %H:%M") 
    } for n in notifications])


# =========================
# MARK NOTIFICATION AS READ
# =========================
@user_bp.route("/notifications/read/<int:notif_id>", methods=["PUT"])
def mark_as_read(notif_id):
    notif = db_session.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        return jsonify({"detail": "Không tìm thấy thông báo"}), 404

    notif.isRead = True
    db_session.commit()

    return jsonify({"message": "Đã đánh dấu đã đọc"})