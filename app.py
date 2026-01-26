from flask import Flask
from flask_jwt_extended import JWTManager
from database import db_session, init_db
from dotenv import load_dotenv
import os
from extensions import csrf

# LOAD ENV
load_dotenv()

# IMPORT EXTENSIONS
from extensions import (
    login_manager,
    csrf,
    limiter,
    talisman
)

# IMPORT API ROUTERS
from routers.user_router import user_bp
from routers.company_router import company_bp
from routers.student_router import student_bp
from routers.recruitment_router import recruitment_bp
from routers.admin_router import admin_bp

# IMPORT VIEW ROUTERS
from view.auth_view import auth_bp
from view.student_view import student_view_bp
from view.company_view import company_view_bp
from view.admin_view import admin_view_bp

# CREATE APP
app = Flask(__name__)

# CORE SECURITY CONFIG
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError("❌ FLASK_SECRET_KEY chưa được cấu hình trong .env")

# JWT CONFIG
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("❌ JWT_SECRET_KEY chưa được cấu hình trong .env")

# 🔥 BẮT BUỘC PHẢI CÓ
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"


app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,   
    JWT_ACCESS_TOKEN_EXPIRES=3600  
)


# INIT EXTENSIONS
login_manager.init_app(app)
csrf.init_app(app)
limiter.init_app(app)

# INIT JWT
jwt = JWTManager(app)

# SECURITY HEADERS
talisman.init_app(
    app,
    content_security_policy={
        "default-src": "'self'",
        "img-src": "*",
        "script-src": "'self' 'unsafe-inline'",
        "style-src": "'self' 'unsafe-inline'",
    },
)

# set login view using setattr to satisfy type checkers
setattr(login_manager, "login_view", "auth_view.login")
login_manager.login_message = "Vui lòng đăng nhập để tiếp tục"

# REGISTER API ROUTERS
app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(company_bp, url_prefix="/api")
app.register_blueprint(student_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api")
app.register_blueprint(recruitment_bp, url_prefix="/api")


csrf.exempt(user_bp)
csrf.exempt(company_bp)
csrf.exempt(student_bp)
csrf.exempt(admin_bp)
csrf.exempt(recruitment_bp)


csrf.exempt(auth_bp)
csrf.exempt(student_view_bp)
csrf.exempt(company_view_bp)
csrf.exempt(admin_view_bp)


# REGISTER VIEW ROUTERS
app.register_blueprint(auth_bp)
app.register_blueprint(student_view_bp)
app.register_blueprint(company_view_bp)
app.register_blueprint(admin_view_bp)

# DB SESSION CLEANUP
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# RUN SERVER
if __name__ == "__main__":
    init_db()
    print("🚀 Server đang chạy tại: http://127.0.0.1:8001")
    app.run(debug=True, port=8001)


