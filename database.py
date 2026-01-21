from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = "sqlite:///./A-platform-that-supports-businesses-in-competency-based-recruitment/RecruitmentApp.db"

engine = create_engine(DATABASE_URL, echo=True)
# Sử dụng scoped_session để đảm bảo an toàn luồng trong Flask
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    from models.base import Base
    import models # Import để nhận diện tất cả các bảng
    Base.metadata.create_all(bind=engine)