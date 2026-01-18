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
## ✨ Key Features (Tính năng chính)

* **👥 Quản lý người dùng (Users):**
    * Phân quyền: Admin, Doanh nghiệp (Company), Sinh viên/Ứng viên (Student).
    * Đăng ký, đăng nhập, xác thực.
* **🏢 Dành cho Doanh nghiệp:**
    * Đăng tin tuyển dụng (Job Posting).
    * Quản lý hồ sơ ứng tuyển.
    * Tìm kiếm ứng viên theo năng lực.
* **🎓 Dành cho Ứng viên:**
    * Tạo và quản lý hồ sơ cá nhân (Profile).
    * Tìm kiếm việc làm và nộp đơn ứng tuyển.
    * Thực hiện bài đánh giá năng lực (Competency Assessment).
* **⚙️ Hệ thống:**
    * Kiến trúc Clean Architecture dễ mở rộng.
    * API chuẩn RESTful.
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
 * Bước 4: Cấu hình biến môi trường (.env)
 ```
    # Flask settings
    FLASK_ENV=development
    SECRET_KEY=your_secret_key_change_me
    
    # Database settings (SQLite)
    DATABASE_URI="sqlite:///RecruitmentApp.db"
  ```
 * Bước 5: Chạy ứng dụng
   ### Run:
```
    python app.py
```
## 🗄️ Database & ORM (SQLAlchemy)
Hệ thống sử dụng SQLAlchemy (ORM) để ánh xạ đối tượng (OOP) vào cơ sở dữ liệu.
Ánh xạ: 1 Class (trong models/) ↔ 1 Bảng (Database).
Quan hệ chính:

Candidate - Skill (n-n)

JobPosition - Skill (n-n)

Candidate - Assessment (1-n)

Candidate - InterviewResult (1-n)
## 📊 Sequence Diagram (Luồng xử lý)
Mô tả quy trình xử lý một Request theo Clean Architecture:
```
sequenceDiagram
    participant Actor
    participant WebApp as Web App (Flask)
    participant Controller as Router/Controller
    participant Services as Service Layer
    participant Domain as Domain Layer
    participant Infra as Infrastructure/Repo
    participant DB as SQLite Database

    Note over WebApp, DB: Request Flow
    Actor->>WebApp: 1. Request recruitment processing
    WebApp->>Controller: 2. Forward to Router
    Controller->>Services: 3. Call Service logic
    Services->>Domain: 4. Apply Business Rules
    Domain->>Infra: 5. Request Data Access
    Infra->>DB: 6. Execute Query (ORM)

    Note over DB, WebApp: Response Flow
    DB-->>Infra: 7. Return Raw Data
    Infra-->>Domain: 8. Return Models
    Domain-->>Services: 9. Return Processed Data
    Services-->>Controller: 10. Return DTO/Schema
    Controller-->>WebApp: 11. JSON Response
    WebApp-->>Actor: 12. Render Result
```
