import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "RecruitmentApp.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

def init_db():
    from models.base import Base
    import models
    Base.metadata.create_all(bind=engine)
