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
 * Bước 4: Chạy mã xử lý dữ liệu
 ### Run
 ```
 python app.py
```
## Create file .env in folder /src/.env

### Flask settings

FLASK_ENV=development SECRET_KEY=your_secret_key

### SQL Server settings

DB_USER=sa DB_PASSWORD=Aa@123456 DB_HOST=127.0.0.1 DB_PORT=1433 DB_NAME=RecruitmentDB

DATABASE_URI="mssql+pymssql://sa:Aa2123456@127.0.0.1:1433/RecruitmentDB"

### Pull image MS SQL Server

docker pull mcr.microsoft.com/mssql/server:2025-latest
## Pull image MS SQL Server
```bash
docker pull mcr.microsoft.com/mssql/server:2025-latest
```
## Install MS SQL server in docker (Cài đặt MS SQL Server bằng Docker)
```bash
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Aa@123456" -p 1433:1433 --name recruitment_sql -d mcr.microsoft.com/mssql/server:2025-latest
```
## Test connect SQL server
```bash
docker ps
```
- Kiểm tra kết nối từ Flask thông qua DATABASE-URI
- Nếu kết nối thành công -> hệ thống sẵn sàng hoạt động

## ORM Flask (from sqlalchemy.orm )

Object Relational Mapping

Ánh xạ 1 class (OOP) trong src/infrastructure/models
-> 1 bảng trong cơ sở dữ liệu
-> Ánh xạ các mối quan hệ (Relational)
-> Khoá ngoại CSDL

Các quan hệ chính trong hệ thống tuyển dụng:

Candidate - Skill (n-n)

JobPosition - Skill (n-n)

Candidate - Assessment (1-n)

Candidate - InterviewResult (1-n)

### Clean Architecture Sequence Diagram
@startuml title Recruitment System Clean Architecture Sequence Diagram

' Define participants in oder of appearance actor Actor participant "Web App" participant "Controller" participant "Services" participant "Domain" participant "Infrastructure" participant "Database"

'--- Message Flow ---

'1. Initial Request Actor -> "Web App" : Request recruitment processing activate "Web App"

'2. Forwarding to Controller "Web App" -> "Controller" activate "Controller"

'3. Calling the Service Layer "Controller" -> "Services" activate "Services"

'4. Interacting with the Domain Layer "Services" -> "Domain" activate "Domain" note over "Domain" : Recruitment business rules\nCompetency evaluation logic

'5. Interacting with Infrastructure "Domain" -> "Infrastructure" activate "Infrastructure" note over "Infrastructure" : ORM models\nRepository implementation

'6. Database Query "Infrastructure" -> "Database" activate "Database"

' --- Response Flow (Return Messages) ---

'7. Database returns data "Database" --> "Infrastructure" deactivate "Database"

'8. Infrastructure returns to Domain "Infrastructure" --> "Domain" deactivate "Infrastructure"

'9. Domain returns to Services "Domain" --> "Services" deactivate "Domain"

'10. Services returns to Controller "Services" --> "Controller" deactivate "Services"

'11. Controller returns to Web App "Controller" --> "Web App" deactivate "Controller"

'12. Final data rendering to Actor "Web App" --> Actor note left of "Web App" : Render recruitment result  
deactivate "Web App"

@enduml