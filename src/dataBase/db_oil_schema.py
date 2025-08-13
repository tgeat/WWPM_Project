from sqlalchemy import Column, Integer, String, Date, Text, create_engine, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.declarative import declared_attr

# 数据库连接配置
DB_URI = "mysql+pymysql://root:112224@127.0.0.1:3306/water_report?charset=utf8mb4"


engine = create_engine(DB_URI, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

Base = declarative_base()

class OilWellBase:
    """油井数据基类，定义公共字段"""

    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, autoincrement=True)  # 自增ID主键

    @declared_attr
    def well_code(cls):
        return Column(String(50), nullable=False)  # 井号

    @declared_attr
    def platform(cls):
        return Column(String(50), nullable=False)  # 平台

    @declared_attr
    def create_time(cls):
        return Column(Date, nullable=False)

    # 唯一约束（平台+井号+日期）
    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('platform', 'well_code', 'create_time',
                             name=f'uq_{cls.__tablename__}_unique'),
        )

    # 其他字段
    total_bucket_sign = Column(String(50))  # 是否合量斗数
    total_bucket = Column(String(50))  # 合量斗数
    time_sign = Column(String(50))  # 时间标记
    oil_pressure = Column(String(50))  # 油压
    casing_pressure = Column(String(50))  # 套压
    back_pressure = Column(String(50))  # 回压
    press_data = Column(String(50))  # 憋压数据
    prod_hours = Column(String(50))  # 生产时间
    a2_stroke = Column(String(50))  # A2冲程
    a2_frequency = Column(String(50))  # A2冲次
    work_stroke = Column(String(50))  # 功图冲次
    effective_stroke = Column(String(50))  # 有效排液冲程
    fill_coeff_test = Column(String(50))  # 充满系数
    lab_water_cut = Column(String(50))  # 化验含水
    reported_water = Column(String(50))  # 上报含水
    fill_coeff_liquid = Column(String(50))  # 充满系数液量
    last_tubing_time = Column(String(50))  # 上次动管柱时间
    pump_diameter = Column(String(50))  # 泵径
    block = Column(String(50))  # 区块
    transformer = Column(String(50))  # 变压器
    remark = Column(Text)  # 备注
    liquid_per_bucket = Column(String(50))  # 每桶液量
    sum_value = Column(String(50))  # 合计值
    liquid1 = Column(String(50))  # 液量1
    production_coeff = Column(String(50))  # 生产系数
    a2_24h_liquid = Column(String(50))  # A2 24h液量
    liquid2 = Column(String(50))  # 液量2
    oil_volume = Column(String(50))  # 油量
    fluctuation_range = Column(String(50))  # 波动范围
    shutdown_time = Column(String(50))  # 停产时间
    theory_diff = Column(String(50))  # 理论差值
    theory_displacement = Column(String(50))  # 理论排量
    k_value = Column(String(50))  # K值
    daily_liquid = Column(String(50))  # 日产液
    daily_oil = Column(String(50))  # 日产油
    well_times = Column(String(50))  # 井次数
    production_time = Column(String(50))  # 时间
    total_oil = Column(String(50))  # 总产油

class OilWellReports(Base, OilWellBase):
    """油井数据备份表模型（历史报表）"""
    __tablename__ = "oil_well_reports"

class FormulaData(Base):
    __tablename__ = 'formula_datas'
    id = Column(Integer, primary_key=True)
    formula = Column(String(255), nullable=False)