# A platform that supports businesses in competency-based recruitment

Đây là phần mềm hỗ trợ doanh nghiệp kết nối với các ứng viên tiềm năng dựa trên mô hình đánh giá năng lực.

## 🏗 Architecture (Cấu trúc dự án)

Dưới đây là sơ đồ cấu trúc thư mục của dự án:

```text
project_recruitment/
├── models/                 # Chứa các định nghĩa database models (SQLAlchemy)
│   ├── app_models.py
│   ├── job_models.py
│   ├── user_models.py
│   └── base.py
├── routers/                # Chứa các API endpoints (FastAPI)
│   ├── recruitment_router.py
│   └── user_router.py
├── schemas/                # Chứa các data validation (Pydantic models)
│   ├── app_schemas.py
│   ├── job_schemas.py
│   └── user_schemas.py
├── database.py             # Cấu hình kết nối cơ sở dữ liệu
├── main.py                 # File thực thi chính (Entry point)
├── frontend.py             # Giao diện người dùng (nếu có)
├── seed_data.py            # File khởi tạo dữ liệu mẫu
├── requirements.txt        # Danh sách các thư viện cần cài đặt
└── .gitignore              # Cấu hình các file Git bỏ qua
