# db_schema.py
from sqlalchemy import (
    Column, String, Integer, BigInteger, Date, DECIMAL, ForeignKey,
    UniqueConstraint, TIMESTAMP, func
)
from sqlalchemy.orm import declarative_base, relationship

# Absolute imports allow this module to be imported without relying on package
# relative imports.
from config.db_config import SessionLocal

__all__ = ["SessionLocal"]
Base = declarative_base()


# 权限枚举
# class PermissionEnum(enum.Enum):
#     Admin = "Admin"
#     User = "User"
#     Advanced = "Advanced"

# 用户账户表
class UserAccount(Base):
    __tablename__ = "user_account"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    permission = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


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
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("prod_team.team_id"), nullable=False)
    room_no = Column(String(10), nullable=False)
    is_injection_room = Column(Integer, default=0)  # 1=是，0=否

    team = relationship("ProdTeam", back_populates="rooms")
    bao = relationship("Bao", back_populates="room")   # 一间对多报
    __table_args__ = (UniqueConstraint("team_id", "room_no", name="uk_team_roomNo"),)

# ---------- 4. 报的类型 ----------
class Bao(Base):
    __tablename__ = "bao_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bao_typeid = Column(String(20), nullable=False)
    room_id = Column(Integer, ForeignKey("meter_room.id"), nullable=False)

    room = relationship("MeterRoom", back_populates="bao")
    platforms = relationship("Platformer", back_populates="bao")  # 多平台
    wells = relationship("Well", back_populates="bao")            # 水报下直接挂井


# ---------- 5. 平台 ----------
class Platformer(Base):
    __tablename__ = "platformer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platformer_id = Column(String(50), nullable=False)
    bao_id = Column(Integer, ForeignKey("bao_type.id"), nullable=False)

    bao = relationship("Bao", back_populates="platforms")
    wells = relationship("Well", back_populates="platform")


# ---------- 6. 井 ----------
class Well(Base):
    __tablename__ = "well"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("meter_room.id"), nullable=False)
    bao_id = Column(Integer, ForeignKey("bao_type.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platformer.id"), nullable=True)
    well_code = Column(String(30), nullable=False)

    room = relationship("MeterRoom")
    bao = relationship("Bao", back_populates="wells")
    platform = relationship("Platformer", back_populates="wells")
    reports = relationship("DailyReport", back_populates="well")
    oil_well_reports = relationship("OilWellDatas", back_populates="well")
    __table_args__ = (
        UniqueConstraint("room_id", "well_code", name="uk_room_wellCode"),
    )

# ---------- 8. 油井数据 ----------
class OilWellDatas(Base):
    __tablename__ = "oil_well_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(BigInteger, ForeignKey("well.id"), nullable=False)         #新增
    create_time = Column(Date)
    well_code = Column(String(50))
    platform = Column(String(50))
    oil_pressure = Column(String(50))
    casing_pressure = Column(String(50))
    back_pressure = Column(String(50))
    time_sign = Column(String(50))
    total_bucket_sign = Column(String(10))
    total_bucket = Column(String(50))
    press_data = Column(String(50))
    prod_hours = Column(String(50))
    a2_stroke = Column(String(50))
    a2_frequency = Column(String(50))
    work_stroke = Column(String(50))
    effective_stroke = Column(String(50))
    fill_coeff_test = Column(String(50))
    lab_water_cut = Column(String(50))
    reported_water = Column(String(50))
    fill_coeff_liquid = Column(String(50))
    last_tubing_time = Column(String(50))
    pump_diameter = Column(String(50))
    block = Column(String(50))
    transformer = Column(String(50))
    remark = Column(String)
    liquid_per_bucket = Column(String(50))
    sum_value = Column(String(50))
    liquid1 = Column(String(50))
    production_coeff = Column(String(50))
    a2_24h_liquid = Column(String(50))
    liquid2 = Column(String(50))
    oil_volume = Column(String(50))
    fluctuation_range = Column(String(50))
    shutdown_time = Column(String(50))
    theory_diff = Column(String(50))
    theory_displacement = Column(String(50))
    k_value = Column(String(50))
    daily_liquid = Column(String(50))
    daily_oil = Column(String(50))
    well_times = Column(String(50))
    production_time = Column(String(50))
    total_oil = Column(String(50))
    well = relationship("Well", back_populates="oil_well_reports")
    __table_args__ = (UniqueConstraint("well_id", "create_time", name="uk_well_date"),)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# ---------- 7. 水报 ----------
class DailyReport(Base):
    __tablename__ = "daily_report"

    report_id = Column(BigInteger, primary_key=True, autoincrement=True)
    well_id = Column(BigInteger, ForeignKey("well.id"), nullable=False)
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

class FormulaData(Base):
    # 从db_oil_schema.py中移入
    __tablename__ = "formula_data"
    id = Column(Integer, primary_key=True)
    formula = Column(String(255), nullable=False)