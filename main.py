from flask import Flask, jsonify
from flask_cors import CORS
from database import db_session, init_db
from routers.user_router import user_bp
from routers.recruitment_router import recruitment_bp
from routers.student_router import student_bp
from routers.company_router import company_bp
from routers.admin_router import admin_bp


app = Flask(__name__)
CORS(app) # Cho phép Frontend (Streamlit/React) gọi API
# Khởi tạo DB
init_db()
# Đăng ký các cụm API
app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(recruitment_bp, url_prefix="/api")
app.register_blueprint(student_bp, url_prefix="/api")
app.register_blueprint(company_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api")
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
@app.route("/")
def root():
    return jsonify({"message": "User API is running!"})
if __name__ == "__main__":
    app.run(debug=True, port=8000)