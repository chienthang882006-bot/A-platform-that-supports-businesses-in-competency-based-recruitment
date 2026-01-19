from flask import Flask
from database import db_session, init_db
from dotenv import load_dotenv
import os

load_dotenv()
# Import các API Routers (Backend)
from routers.user_router import user_bp
from routers.company_router import company_bp
from routers.student_router import student_bp

# Import các View Routers (Frontend - MỚI)
from view.auth_view import auth_bp
from view.student_view import student_view_bp
from view.company_view import company_view_bp
from view.admin_view import admin_view_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("FLASK_SECRET_KEY chưa được cấu hình trong .env")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False  
)

# === ĐĂNG KÝ API ROUTERS (PREFIX /api) ===
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(company_bp, url_prefix='/api')
app.register_blueprint(student_bp, url_prefix='/api')

# === ĐĂNG KÝ VIEW ROUTERS (KHÔNG CÓ PREFIX HOẶC PREFIX THEO LOGIC) ===
app.register_blueprint(auth_bp)
app.register_blueprint(student_view_bp)
app.register_blueprint(company_view_bp)
app.register_blueprint(admin_view_bp)

# === TỰ ĐỘNG ĐÓNG DB SESSION ===
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    init_db() 
    print("🚀 Server đang chạy tại: http://127.0.0.1:8001")
    app.run(debug=True, port=8001)