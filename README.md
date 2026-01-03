# Recruitment System - Clean Architecture

Dự án quản lý tuyển dụng được xây dựng trên nền tảng Python Flask, áp dụng kiến trúc phân tầng (Clean Architecture) để đảm bảo tính mở rộng và dễ bảo trì.

## 🏗️ System Architecture (Cấu trúc dự án)

Dưới đây là sơ đồ tổ chức mã nguồn theo đúng cấu trúc thư mục hiện tại của dự án:

```text
scr/                            # Thư mục gốc chứa mã nguồn của bạn
├── api/                        # Tầng giao tiếp (Interface)
│   ├── router/            # Điều hướng Request (Từ folder 'routers' cũ)
│   │   ├── user_router.py         
│   │   ├── recruitment_router.py  
│   │   ├── student_router.py      
│   │   └── company_router.py      
│   └── schemas/                # Kiểm tra dữ liệu (Từ folder 'schemas' cũ)
│       ├── user_schemas.py        
│       ├── job_schemas.py         
│       └── app_schemas.py         
├── infrastructure/             # Tầng hạ tầng kỹ thuật
│   ├── databases/              # Cấu hình kết nối
│   │   └── database.py         # Quản lý Session và Engine
│   └── models/                 # Định nghĩa bảng Database
│       ├── base.py             # Lớp cơ sở cho ORM
│       ├── user_models.py      
│       ├── job_models.py       
│       └── app_models.py       
├── main.py                     # Điểm khởi chạy ứng dụng Flask
├── seed_data.py                # Tệp khởi tạo dữ liệu mẫu
└── app.py                      # Cấu hình ứng dụng
├── .gitignore                  # Quản lý Git
├── requirements.txt            # Danh sách thư viện cài đặt
└── RecruitmentApp.db           # Cơ sở dữ liệu SQLite hiện tại
