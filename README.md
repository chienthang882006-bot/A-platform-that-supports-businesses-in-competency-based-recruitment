# Recruitment System - Clean Architecture

Dự án quản lý tuyển dụng được xây dựng trên nền tảng Python Flask, áp dụng kiến trúc phân tầng (Clean Architecture) để đảm bảo tính mở rộng và dễ bảo trì.

## 🏗️ System Architecture (Cấu trúc dự án)

Dưới đây là sơ đồ tổ chức mã nguồn theo đúng cấu trúc thư mục hiện tại của dự án:

```text
scr/                                # Thư mục gốc chứa mã nguồn của bạn                      
│   ├── router/                     # Điều hướng Request
│   │   ├── user_router.py         
│   │   ├── recruitment_router.py  
│   │   ├── student_router.py      
│   │   └── company_router.py      
│   ├── schemas/                    # Kiểm tra dữ liệu
│   │   ├── user_schemas.py        
│   │   ├── job_schemas.py         
│   │   └── app_schemas.py         
│   │         
│   ├── models/                     # Định nghĩa bảng Database
│   │   ├── base.py                 # Lớp cơ sở cho ORM
│   │   ├── user_models.py      
│   │   ├── job_models.py       
│   │   └── app_models.py       
│   ├── main.py                     # Điểm khởi chạy ứng dụng Flask
│   ├── seed_data.py                # Tệp khởi tạo dữ liệu mẫu
│   ├── app.py                      # Cấu hình ứng dụng
│   ├── database.py                 # Quản lý Session và Engine
│   └── RecruitmentApp.db           # Cơ sở dữ liệu SQLite hiện tại
├── .gitignore                      # Quản lý Git
└── requirements.txt                # Danh sách thư viện cài đặt
```

## Download source code (CMD)
```bash
  git clone https://github.com/chienthang882006-bot/A-platform-that-supports-businesses-in-competency-based-recruitment.git
```
## Kiểm tra đã cài python đã cài đặt trên máy chưa
```bash
  python --version
```
## Run app
* Bước 1: Tạo môi trường ảo co Python (phiên bản 3.x)
  ### Windows:
  ```
    py -m venv .venv
  ```
  ### Unix/MacOS:
  ```
    python3 -m venv .venv
  ```
  * Bước 2: Kích hoạt môi trường:
  ### Windows:
  ```
     .venv\Scripts\activate.ps1
  ```
  ### Nếu xảy ra lỗi active .venv trên winos run powershell -->Administrator
    ```
     Set-ExecutionPolicy RemoteSigned -Force
  ```
    ### Unix/MacOS:
  ```
    source .venv/bin/activate
  ```
  * Bước 3: Cài đặt các thư viện cần thiết
   ### Install:
  ```
    pip install -r requirements.txt
  ```
