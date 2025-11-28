# App/core/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# 예: mysql+pymysql://user:password@main-db:3306/mydb
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # 개발 단계에서만 쓰는 기본값 예시
    DATABASE_URL = "mysql+pymysql://root:password@main-db:3306/mydb?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 의존성 주입용 세션
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
