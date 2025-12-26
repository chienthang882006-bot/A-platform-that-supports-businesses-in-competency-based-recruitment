from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models.base import Base

# Import routers
from routers import user_router, recruitment_router

# Tạo bảng database nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hệ thống Tuyển dụng API")

# --- CẤU HÌNH CORS (Cho phép Frontend kết nối) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép mọi nguồn kết nối (trong thực tế nên giới hạn)
    allow_credentials=True,
    allow_methods=["*"], # Cho phép tất cả các phương thức (GET, POST...)
    allow_headers=["*"],
)

# Đăng ký các router
app.include_router(user_router.router)
app.include_router(recruitment_router.router)

@app.get("/")
def root():
    return {"message": "Server đang chạy thành công!"}