from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt,
    get_jwt_identity
)
from database import db_session
from models.user_models import (
    User, Student, Company, CompanyProfile,
    StudentProfile, UserRole
)
from models.app_models import Notification
import re
from time import time

bcrypt = Bcrypt()
user_bp = Blueprint("user_router", __name__)

# AUTH HELPERS (JWT)
def require_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"detail": "Forbidden"}), 403
    return None

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LOGIN_ATTEMPTS = {}
MAX_ATTEMPTS = 5
BLOCK_TIME = 300  # 5 phút

def is_blocked(key):
    data = LOGIN_ATTEMPTS.get(key)
    if not data:
        return False
    attempts, first_time = data
    if attempts >= MAX_ATTEMPTS and time() - first_time < BLOCK_TIME:
        return True
    if time() - first_time >= BLOCK_TIME:
        LOGIN_ATTEMPTS.pop(key, None)
    return False

def is_valid_email(email: str) -> bool:
    if not email or len(email) > 255:
        return False
    return bool(EMAIL_REGEX.match(email))

def is_strong_password(password: str) -> bool:
    if not password or len(password) < 6 or len(password) > 128:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*()_+=\-]", password):
        return False
    return True


# GET ALL USERS (ADMIN)
@user_bp.route("/users/", methods=["GET"])
@jwt_required()
def get_users():
    auth = require_admin()
    if auth:
        return auth

    users = db_session.query(User).all()
    return jsonify([{
        "id": u.id,
        "email": u.email,
        "role": u.role.value,
        "status": u.status,
        "createdAt": u.createdAt.isoformat()
    } for u in users])


# REGISTER
@user_bp.route("/users/", methods=["POST"])
def create_user():
    data = request.json or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role_str = data.get("role", "student")

    if not is_valid_email(email):
        return jsonify({"detail": "Email không hợp lệ"}), 400

    if not is_strong_password(password):
        return jsonify({
            "detail": "Mật khẩu phải ≥ 6 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt"
        }), 400

    if not email or not password:
        return jsonify({"detail": "Thiếu email hoặc mật khẩu"}), 400

    if db_session.query(User).filter(User.email == email).first():
        return jsonify({"detail": "Email đã tồn tại"}), 400

    try:
        try:
            role_enum = UserRole(role_str)
        except ValueError:
            role_enum = UserRole.STUDENT

        new_user = User(
            email=email,
            password=bcrypt.generate_password_hash(password).decode("utf-8"),
            role=role_enum,
            status="active"
        )
        db_session.add(new_user)
        db_session.flush()

        if role_enum == UserRole.STUDENT:
            student = Student(
                userId=new_user.id,
                fullName=email.split("@")[0],
                major="Chưa cập nhật"
            )
            db_session.add(student)
            db_session.flush()
            db_session.add(StudentProfile(studentId=student.id))

        elif role_enum == UserRole.COMPANY:
            company = Company(
                userId=new_user.id,
                companyName=email.split("@")[0]
            )
            db_session.add(company)
            db_session.flush()
            db_session.add(CompanyProfile(companyId=company.id))

        db_session.commit()
        return jsonify({
            "id": new_user.id,
            "email": new_user.email,
            "role": new_user.role.value,
            "message": "Đăng ký thành công"
        }), 201

    except Exception as e:
        db_session.rollback()
        return jsonify({"detail": f"Lỗi server: {str(e)}"}), 500


# LOGIN (JWT)
@user_bp.route("/login/", methods=["POST"])
def login():
    data = request.json or {}
    ip = request.remote_addr
    email = data.get("email", "").strip()
    key = f"{ip}:{email}"
    password = data.get("password")
    
    if is_blocked(key):
        return jsonify({
            "detail": "Quá nhiều lần đăng nhập sai. Vui lòng thử lại sau."
        }), 429
        
    user = db_session.query(User).filter(User.email == email).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        if key not in LOGIN_ATTEMPTS:
            LOGIN_ATTEMPTS[key] = (1, time())
        else:
            LOGIN_ATTEMPTS[key] = (
                LOGIN_ATTEMPTS[key][0] + 1,
                LOGIN_ATTEMPTS[key][1]
            )
        return jsonify({"detail": "Sai tài khoản hoặc mật khẩu"}), 401

    if user.status != "active":
        return jsonify({"detail": "Tài khoản đã bị khóa"}), 403
    
    LOGIN_ATTEMPTS.pop(key, None)

    access_token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role.value}
    )

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value
        }
    }), 200

# GET NOTIFICATIONS
@user_bp.route("/notifications/<int:user_id>", methods=["GET"])
@jwt_required()
def get_notifications(user_id):
    if get_jwt_identity() != user_id:
        return jsonify({"detail": "Forbidden"}), 403

    notifications = db_session.query(Notification).filter(
        Notification.userId == user_id
    ).order_by(Notification.createdAt.desc()).all()

    return jsonify([{
        "id": n.id,
        "content": n.content,
        "isRead": n.isRead,
        "createdAt": n.createdAt.strftime("%Y-%m-%d %H:%M")
    } for n in notifications])


# MARK NOTIFICATION AS READ
@user_bp.route("/notifications/read/<int:notif_id>", methods=["PUT"])
@jwt_required()
def mark_as_read(notif_id):
    notif = db_session.query(Notification).filter(
        Notification.id == notif_id
    ).first()

    if not notif:
        return jsonify({"detail": "Không tìm thấy thông báo"}), 404

    if notif.userId != get_jwt_identity():
        return jsonify({"detail": "Forbidden"}), 403

    notif.isRead = True
    db_session.commit()
    return jsonify({"message": "Đã đánh dấu đã đọc"})
