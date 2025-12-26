from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Bạn có thể thay đổi đường dẫn này thành MySQL hoặc PostgreSQL
DATABASE_URL = "sqlite:///./RecruitmentApp.db"

engine = create_engine(DATABASE_URL, echo=True) # echo=True để log lệnh SQL ra màn hình debug
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)