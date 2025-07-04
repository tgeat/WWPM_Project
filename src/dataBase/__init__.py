# db_schema.py
from sqlalchemy import (
    Column, String, Integer, BigInteger, Date, DECIMAL, ForeignKey,
    UniqueConstraint, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ---------- 数据库 URI ----------
DB_URI = "mysql+pymysql://user:password@127.0.0.1:3306/water_report?charset=utf8mb4"

# ---------- 引擎 & 会话 ----------
engine = create_engine(DB_URI, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ---------- 1. 作业区 ----------
class WorkArea(Base):
    __tablename__ = "work_area"
    area_id = Column(Integer, primary_key=True, autoincrement=True)
    area_name = Column(String(30), unique=True, nullable=False)
    teams = relationship("ProdTeam", back_populates="area")


# ---------- 2. 注采班 ----------
class ProdTeam(Base):
    __tablename__ = "prod_team"
    team_id = Column(Integer, primary_key=True, autoincrement=True)
    area_id = Column(Integer, ForeignKey("work_area.area_id"), nullable=False)
    team_name = Column(String(30), nullable=False)
    team_no = Column(Integer, nullable=False)
    area = relationship("WorkArea", back_populates="teams")
    rooms = relationship("MeterRoom", back_populates="team")
    __table_args__ = (UniqueConstraint("area_id", "team_no", name="uk_area_teamNo"),)


# ---------- 3. 计量间 / 注水间 ----------
class MeterRoom(Base):
    __tablename__ = "meter_room"
    room_id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("prod_team.team_id"), nullable=False)
    room_no = Column(String(10), nullable=False)
    is_injection_room = Column(Integer, default=0)
    team = relationship("ProdTeam", back_populates="rooms")
    wells = relationship("Well", back_populates="room")
    __table_args__ = (UniqueConstraint("team_id", "room_no", name="uk_team_roomNo"),)


# ---------- 4. 井 ----------
class Well(Base):
    __tablename__ = "well"
    well_id = Column(BigInteger, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("meter_room.room_id"), nullable=False)
    well_code = Column(String(30), nullable=False)
    room = relationship("MeterRoom", back_populates="wells")
    reports = relationship("DailyReport", back_populates="well")
    __table_args__ = (UniqueConstraint("room_id", "well_code", name="uk_room_wellCode"),)


# ---------- 5. 日报 ----------
class DailyReport(Base):
    __tablename__ = "daily_report"
    report_id = Column(BigInteger, primary_key=True, autoincrement=True)
    well_id = Column(BigInteger, ForeignKey("well.well_id"), nullable=False)
    report_date = Column(Date, nullable=False)
    injection_mode = Column(String(20))
    prod_hours = Column(Integer)
    trunk_pressure = Column(DECIMAL(4, 1))
    oil_pressure = Column(DECIMAL(4, 1))
    casing_pressure = Column(DECIMAL(4, 1))
    wellhead_pressure = Column(DECIMAL(4, 1))
    plan_inject = Column(DECIMAL(6, 2))
    actual_inject = Column(DECIMAL(6, 2))
    remark = Column(String(100))
    meter_stage1 = Column(DECIMAL(10, 2))
    meter_stage2 = Column(DECIMAL(10, 2))
    meter_stage3 = Column(DECIMAL(10, 2))
    well = relationship("Well", back_populates="reports")
    __table_args__ = (UniqueConstraint("well_id", "report_date", name="uk_well_date"),)


# ---------- 首次建表请取消下一行的注释 ----------
# Base.metadata.create_all(engine)
