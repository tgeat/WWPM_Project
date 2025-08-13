from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URI = "mysql+pymysql://root:112224@127.0.0.1:3306/water_report?charset=utf8mb4"

engine = create_engine(DB_URI, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
