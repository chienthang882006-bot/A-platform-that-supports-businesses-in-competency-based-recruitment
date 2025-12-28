from flask import Blueprint, request, jsonify
from scr.database import db_session
from models.user_models import User, UserRole, Student, Notification
from datetime import datetime
from models.user_models import Company

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
# CREATE USER (REGISTER)
# =========================
@user_bp.route("/users/", methods=["POST"])
def create_user():
    data = request.json

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"detail": "Thiếu email hoặc mật khẩu"}), 400

    # Check duplicate email
    if db_session.query(User).filter(User.email == data["email"]).first():
        return jsonify({"detail": "Email đã tồn tại"}), 400

    # Parse role
    try:
        role_enum = UserRole(data.get("role", "student").lower())
    except ValueError:
        role_enum = UserRole.STUDENT

    try:
        # 1️⃣ Create User
        new_user = User(
            email=data["email"],
            password=data["password"],  # ⚠️ demo, nên hash sau
            role=role_enum,
            status="active"
        )
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)

        # 2️⃣ Auto-create STUDENT if role = student
        if new_user.role == UserRole.STUDENT:
            student = Student(
                userId=new_user.id,
                fullName=new_user.email.split("@")[0],
                major=""
            )
            db_session.add(student)
            db_session.commit()
        # 3️⃣ ✅ THÊM ĐOẠN NÀY: Auto-create COMPANY
        if new_user.role == UserRole.COMPANY:
            company = Company(
                userId=new_user.id,
                companyName=new_user.email.split("@")[0],
                description=""
            )
            db_session.add(company)
            db_session.commit()

        return jsonify({
            "id": new_user.id,
            "email": new_user.email,
            "role": new_user.role.value
        }), 201

    except Exception as e:
        db_session.rollback()
        return jsonify({"detail": str(e)}), 500


# =========================
# LOGIN
# =========================
@user_bp.route("/login/", methods=["POST"])
def login():
    data = request.json

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"detail": "Thiếu email hoặc mật khẩu"}), 400

    user = db_session.query(User).filter(
        User.email == data["email"],
        User.password == data["password"]
    ).first()

    if not user:
        return jsonify({"detail": "Email hoặc mật khẩu không đúng"}), 401

    return jsonify({
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "status": user.status
    }), 200


# =========================
# GET NOTIFICATIONS
# =========================
@user_bp.route("/notifications/<int:user_id>", methods=["GET"])
def get_notifications(user_id):
    notifications = db_session.query(Notification).filter(
        Notification.userId == user_id
    ).order_by(Notification.createdAt.desc()).all()

    return jsonify([{
        "id": n.id,
        "content": n.content,
        "isRead": n.isRead,
        "createdAt": n.createdAt.isoformat()
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
