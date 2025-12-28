
├── scr/                               # Thư mục gốc chứa mã nguồn của bạn
│   ├── api/                           # Tầng giao tiếp (Interface)
│   │   ├── controllers/               # Điều hướng Request (Từ folder 'routers' cũ)
│   │   │   ├── user_router.py         #
│   │   │   ├── recruitment_router.py  #
│   │   │   ├── student_router.py      #
│   │   │   └── company_router.py      #
│   │   └── schemas/                   # Kiểm tra dữ liệu (Từ folder 'schemas' cũ)
│   │       ├── user_schemas.py        #
│   │       ├── job_schemas.py         #
│   │       └── app_schemas.py         #
│   ├── infrastructure/                # Tầng hạ tầng kỹ thuật
│   │   ├── databases/                 # Cấu hình kết nối
│   │   │   └── database.py            # Quản lý Session và Engine
│   │   └── models/                    # Định nghĩa bảng Database
│   │       ├── base.py                # Lớp cơ sở cho ORM
│   │       ├── user_models.py         #
│   │       ├── job_models.py          #
│   │       └── app_models.py          #
│   ├── main.py                        # Điểm khởi chạy ứng dụng Flask
│   ├── seed_data.py                   # Tệp khởi tạo dữ liệu mẫu
│   └── app.py                         # Cấu hình ứng dụng
├── .gitignore                         # Quản lý Git
├── requirements.txt                   # Danh sách thư viện cài đặt
└── RecruitmentApp.db                  # Cơ sở dữ liệu SQLite hiện tại
