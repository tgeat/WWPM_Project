import uuid
from dataclasses import dataclass
from datetime import date
from typing import Dict


@dataclass
class OilWellModel:
    """油井数据模型（包含输入表单和计算结果所有字段）"""
    id: str = ""  # 自增ID

    # 核心标识
    well_code: str = ""  # 井号 → 数据库well_code
    platform: str = ""  # 平台 → 数据库platform

    # 压力数据
    oil_pressure: str = ""  # 油压 → 数据库oil_pressure
    casing_pressure: str = ""  # 套压 → 数据库casing_pressure
    back_pressure: str = ""  # 回压 → 数据库back_pressure

    # 生产数据
    time_sign: str = ""  # 时间标记
    prod_hours: str = ""  # 生产时间 → 数据库prod_hours
    a2_stroke: str = ""  # A2冲程 → 数据库a2_stroke
    a2_frequency: str = ""  # A2冲次 → 数据库a2_frequency
    work_stroke: str = ""  # 功图冲次 → 数据库work_stroke
    effective_stroke: str = ""  # 有效排液冲程 → 数据库effective_stroke
    fill_coeff_test: str = ""  # 充满系数 → 数据库fill_coeff_test
    lab_water_cut: str = ""  # 化验含水 → 数据库lab_water_cut
    reported_water: str = ""  # 上报含水 → 数据库reported_water
    fill_coeff_liquid: str = ""  # 充满系数液量 → 数据库fill_coeff_liquid
    last_tubing_time: str = ""  # 上次动管柱时间 → 数据库last_tubing_time

    # 计量数据
    total_bucket: str = ""  # 合量斗数 → 数据库total_bucket
    press_data: str = ""  # 憋压数据 → 数据库press_data

    # 基础信息
    pump_diameter: str = ""  # 泵径 → 数据库pump_diameter
    block: str = ""  # 区块 → 数据库block
    transformer: str = ""  # 变压器 → 数据库transformer
    remark: str = ""  # 备注 → 数据库remark
    well_times: str = "" # 井次 -> 数据库well_times

    # 公式计算结果字段（与table_result对应）
    liquid_per_bucket: str = ""  # 液量/斗数
    sum_value: str = ""  # 合计值
    liquid1: str = ""  # 液量
    production_coeff: str = ""  # 生产系数
    a2_24h_liquid: str = ""  # A2 24h液量
    liquid2: str = ""  # 液量（资料员）
    oil_volume: str = ""  # 油量
    fluctuation_range: str = ""  # 波动范围
    shutdown_time: str = ""  # 停产时间
    theory_diff: str = ""  # 理论排量-液量差值
    theory_displacement: str = ""  # 理论排量
    k_value: str = ""  # K值
    daily_liquid: str = ""  # 日产液
    daily_oil: str = ""  # 日产油
    production_time: str = ""  # 时间
    total_oil: str = ""  # 产油

    # 从视图读取数据（包含两个tab页：输入+计算结果）
    @classmethod
    def from_view(cls, view) -> "OilWellModel":
        return cls(
            # 核心标识
            well_code=view.get_lineEdit_wellNum().text(),
            platform=view.get_lineEdit_injectFuc().text(),

            # 压力数据（输入tab）
            oil_pressure=view.get_lineEdit_oilPres().text(),
            casing_pressure=view.get_lineEdit_casePres().text(),
            back_pressure=view.get_lineEdit_wellOilPres().text(),

            # 生产数据（输入tab）
            time_sign=view.get_lineEdit_10().text(),
            prod_hours=view.get_lineEdit_productLong().text(),
            a2_stroke=view.get_lineEdit_mainLinePres().text(),
            a2_frequency=view.get_lineEdit_2().text(),
            work_stroke=view.get_lineEdit_daliyWater().text(),
            effective_stroke=view.get_lineEdit_totalWater().text(),
            fill_coeff_test=view.get_lineEdit_3().text(),
            lab_water_cut=view.get_lineEdit_testWater().text(),
            reported_water=view.get_lineEdit_4().text(),
            fill_coeff_liquid=view.get_lineEdit_5().text(),
            last_tubing_time=view.get_lineEdit_6().text(),

            # 计量数据（输入tab）
            total_bucket=view.get_lineEdit_firstExecl().text(),
            press_data=view.get_lineEdit_firstWater().text(),

            # 基础信息（输入tab）
            well_times=view.get_lineEdit_nums().text(),
            pump_diameter=view.get_lineEdit_7().text(),
            block=view.get_lineEdit_8().text(),
            transformer=view.get_lineEdit_9().text(),
            remark=view.get_lineEdit_note().text(),

            # 公式计算结果（结果tab）
            liquid_per_bucket=view.get_lineEdit_liquid_bucket().text(),
            sum_value=view.get_lineEdit_sum().text(),
            liquid1=view.get_lineEdit_liquid().text(),
            production_coeff=view.get_lineEdit_distribution_coeff().text(),
            a2_24h_liquid=view.get_lineEdit_a2_24h().text(),
            liquid2=view.get_lineEdit_liquid_data().text(),
            oil_volume=view.get_lineEdit_oil().text(),
            fluctuation_range=view.get_lineEdit_fluctuation_range().text(),
            shutdown_time=view.get_lineEdit_stop_time().text(),
            theory_diff=view.get_lineEdit_theory_diff().text(),
            theory_displacement=view.get_lineEdit_theory_displacement().text(),
            k_value=view.get_lineEdit_k_value().text(),
            daily_liquid=view.get_lineEdit_daily_liquid().text(),
            daily_oil=view.get_lineEdit_daily_oil().text(),
            production_time=view.get_lineEdit_produce_oil().text(),
        )

    # 写回视图（包含两个tab页：输入+计算结果）
    def to_view(self, view) -> None:
        # 核心标识（输入tab）
        view.get_lineEdit_wellNum().setText(self.well_code)
        view.get_lineEdit_injectFuc().setText(self.platform)

        # 压力数据（输入tab）
        view.get_lineEdit_oilPres().setText(self.oil_pressure)
        view.get_lineEdit_casePres().setText(self.casing_pressure)
        view.get_lineEdit_wellOilPres().setText(self.back_pressure)

        # 生产数据（输入tab）
        view.get_lineEdit_10().setText(self.time_sign)
        view.get_lineEdit_productLong().setText(self.prod_hours)
        view.get_lineEdit_mainLinePres().setText(self.a2_stroke)
        view.get_lineEdit_2().setText(self.a2_frequency)
        view.get_lineEdit_daliyWater().setText(self.work_stroke)
        view.get_lineEdit_totalWater().setText(self.effective_stroke)
        view.get_lineEdit_3().setText(self.fill_coeff_test)
        view.get_lineEdit_testWater().setText(self.lab_water_cut)
        view.get_lineEdit_4().setText(self.reported_water)
        view.get_lineEdit_5().setText(self.fill_coeff_liquid)
        view.get_lineEdit_6().setText(self.last_tubing_time)

        # 计量数据（输入tab）
        view.get_lineEdit_firstExecl().setText(self.total_bucket)
        view.get_lineEdit_firstWater().setText(self.press_data)

        # 基础信息（输入tab）
        view.get_lineEdit_7().setText(self.pump_diameter)
        view.get_lineEdit_8().setText(self.block)
        view.get_lineEdit_9().setText(self.transformer)
        view.get_lineEdit_note().setText(self.remark)
        view.get_lineEdit_nums().setText(self.well_times)

        # 公式计算结果（结果tab）
        view.get_lineEdit_liquid_bucket().setText(self.liquid_per_bucket)
        view.get_lineEdit_sum().setText(self.sum_value)
        view.get_lineEdit_liquid().setText(self.liquid1)
        view.get_lineEdit_distribution_coeff().setText(self.production_coeff)
        view.get_lineEdit_a2_24h().setText(self.a2_24h_liquid)
        view.get_lineEdit_liquid_data().setText(self.liquid2)
        view.get_lineEdit_oil().setText(self.oil_volume)
        view.get_lineEdit_fluctuation_range().setText(self.fluctuation_range)
        view.get_lineEdit_stop_time().setText(self.shutdown_time)
        view.get_lineEdit_theory_diff().setText(self.theory_diff)
        view.get_lineEdit_theory_displacement().setText(self.theory_displacement)
        view.get_lineEdit_k_value().setText(self.k_value)
        view.get_lineEdit_daily_liquid().setText(self.daily_liquid)
        view.get_lineEdit_daily_oil().setText(self.daily_oil)
        view.get_lineEdit_time().setText(self.production_time)
        view.get_lineEdit_produce_oil().setText(self.total_oil)

    # 转换为数据库操作字典（包含所有字段）
    def to_db_dict(self) -> Dict[str, str]:
        return {
            # 核心标识
            "well_code": self.well_code,
            "platform": self.platform,

            # 压力数据
            "oil_pressure": self.oil_pressure,
            "casing_pressure": self.casing_pressure,
            "back_pressure": self.back_pressure,

            # 生产数据
            "time_sign": self.time_sign,
            "prod_hours": self.prod_hours,
            "a2_stroke": self.a2_stroke,
            "a2_frequency": self.a2_frequency,
            "work_stroke": self.work_stroke,
            "effective_stroke": self.effective_stroke,
            "fill_coeff_test": self.fill_coeff_test,
            "lab_water_cut": self.lab_water_cut,
            "reported_water": self.reported_water,
            "fill_coeff_liquid": self.fill_coeff_liquid,
            "last_tubing_time": self.last_tubing_time,

            # 计量数据
            "total_bucket": self.total_bucket,
            "press_data": self.press_data,

            # 基础信息
            "pump_diameter": self.pump_diameter,
            "block": self.block,
            "transformer": self.transformer,
            "remark": self.remark,
            "well_times": self.well_times,

            # 公式计算结果
            "liquid_per_bucket": self.liquid_per_bucket,
            "sum_value": self.sum_value,
            "liquid1": self.liquid1,
            "production_coeff": self.production_coeff,
            "a2_24h_liquid": self.a2_24h_liquid,
            "liquid2": self.liquid2,
            "oil_volume": self.oil_volume,
            "fluctuation_range": self.fluctuation_range,
            "shutdown_time": self.shutdown_time,
            "theory_diff": self.theory_diff,
            "theory_displacement": self.theory_displacement,
            "k_value": self.k_value,
            "daily_liquid": self.daily_liquid,
            "daily_oil": self.daily_oil,
            "production_time": self.production_time,
            "total_oil": self.total_oil,
        }

    # 从数据库记录创建模型（包含所有字段）
    @classmethod
    def from_db_record(cls, record: Dict) -> "OilWellModel":
        return cls(
            id=str(record.get("id", "")),

            # 核心标识
            well_code=record.get("well_code", ""),
            platform=record.get("platform", ""),

            # 压力数据
            oil_pressure=record.get("oil_pressure", ""),
            casing_pressure=record.get("casing_pressure", ""),
            back_pressure=record.get("back_pressure", ""),

            # 生产数据
            time_sign=record.get("time_sign", ""),
            prod_hours=record.get("prod_hours", ""),
            a2_stroke=record.get("a2_stroke", ""),
            a2_frequency=record.get("a2_frequency", ""),
            work_stroke=record.get("work_stroke", ""),
            effective_stroke=record.get("effective_stroke", ""),
            fill_coeff_test=record.get("fill_coeff_test", ""),
            lab_water_cut=record.get("lab_water_cut", ""),
            reported_water=record.get("reported_water", ""),
            fill_coeff_liquid=record.get("fill_coeff_liquid", ""),
            last_tubing_time=record.get("last_tubing_time", ""),

            # 计量数据
            total_bucket=record.get("total_bucket", ""),
            press_data=record.get("press_data", ""),

            # 基础信息
            pump_diameter=record.get("pump_diameter", ""),
            block=record.get("block", ""),
            transformer=record.get("transformer", ""),
            remark=record.get("remark", ""),
            well_times=record.get("well_times", ""),

            # 公式计算结果
            liquid_per_bucket=record.get("liquid_per_bucket", ""),
            sum_value=record.get("sum_value", ""),
            liquid1=record.get("liquid1", ""),
            production_coeff=record.get("production_coeff", ""),
            a2_24h_liquid=record.get("a2_24h_liquid", ""),
            liquid2=record.get("liquid2", ""),
            oil_volume=record.get("oil_volume", ""),
            fluctuation_range=record.get("fluctuation_range", ""),
            shutdown_time=record.get("shutdown_time", ""),
            theory_diff=record.get("theory_diff", ""),
            theory_displacement=record.get("theory_displacement", ""),
            k_value=record.get("k_value", ""),
            daily_liquid=record.get("daily_liquid", ""),
            daily_oil=record.get("daily_oil", ""),
            production_time=record.get("production_time", ""),
            total_oil=record.get("total_oil", ""),
        )


class ReportData:
    """完整报表数据结构（与模型字段一一对应）"""

    def __init__(self, platform, well_code):
        # 基础信息
        #self.id = id(self)  # 唯一标识（内存地址）
        self.id = uuid.uuid4().hex
        self.create_time = date.today()  # 创建日期
        self.platform = platform  # 平台
        self.well_code = well_code  # 井号

        self.total_bucket_sign = "是"  # 是否合量斗数，默认为"是"

        # 输入数据（与OilWellModel对应）
        self.oil_pressure = ""  # 油压
        self.casing_pressure = ""  # 套压
        self.back_pressure = ""  # 回压
        self.time_sign = ""  # 时间标记
        self.prod_hours = ""  # 生产时间
        self.a2_stroke = ""  # A2冲程
        self.a2_frequency = ""  # A2冲次
        self.work_stroke = ""  # 功图冲次
        self.effective_stroke = ""  # 有效排液冲程
        self.fill_coeff_test = ""  # 充满系数
        self.lab_water_cut = ""  # 化验含水
        self.reported_water = ""  # 上报含水
        self.fill_coeff_liquid = ""  # 充满系数液量
        self.last_tubing_time = ""  # 上次动管柱时间
        self.total_bucket = ""  # 合量斗数
        self.press_data = ""  # 憋压数据
        self.pump_diameter = ""  # 泵径
        self.block = ""  # 区块
        self.transformer = ""  # 变压器
        self.remark = ""  # 备注
        self.well_times = ""  # 井次

        # 公式计算结果（与OilWellModel对应）
        self.liquid_per_bucket = ""  # 液量/斗数
        self.sum_value = ""  # 合计值
        self.liquid1 = ""  # 液量
        self.production_coeff = ""  # 生产系数
        self.a2_24h_liquid = ""  # A2 24h液量
        self.liquid2 = ""  # 液量（资料员）
        self.oil_volume = ""  # 油量
        self.fluctuation_range = ""  # 波动范围
        self.shutdown_time = ""  # 停产时间
        self.theory_diff = ""  # 理论排量-液量差值
        self.theory_displacement = ""  # 理论排量
        self.k_value = ""  # K值
        self.daily_liquid = ""  # 日产液
        self.daily_oil = ""  # 日产油
        self.production_time = ""  # 时间
        self.total_oil = ""  # 产油

    def to_dict(self):
        """转换为字典用于表格展示和存储"""
        return {
            "id": self.id,
            "create_time": self.create_time,
            "platform": self.platform,
            "well_code": self.well_code,
            "oil_pressure": self.oil_pressure,
            "casing_pressure": self.casing_pressure,
            "back_pressure": self.back_pressure,
            "time_sign": self.time_sign,
            "prod_hours": self.prod_hours,
            "a2_stroke": self.a2_stroke,
            "a2_frequency": self.a2_frequency,
            "work_stroke": self.work_stroke,
            "effective_stroke": self.effective_stroke,
            "fill_coeff_test": self.fill_coeff_test,
            "lab_water_cut": self.lab_water_cut,
            "reported_water": self.reported_water,
            "fill_coeff_liquid": self.fill_coeff_liquid,
            "last_tubing_time": self.last_tubing_time,
            "total_bucket_sign": self.total_bucket_sign,
            "total_bucket": self.total_bucket,
            "press_data": self.press_data,
            "pump_diameter": self.pump_diameter,
            "block": self.block,
            "transformer": self.transformer,
            "remark": self.remark,
            "well_times": self.well_times,
            "liquid_per_bucket": self.liquid_per_bucket,
            "sum_value": self.sum_value,
            "liquid1": self.liquid1,
            "production_coeff": self.production_coeff,
            "a2_24h_liquid": self.a2_24h_liquid,
            "liquid2": self.liquid2,
            "oil_volume": self.oil_volume,
            "fluctuation_range": self.fluctuation_range,
            "shutdown_time": self.shutdown_time,
            "theory_diff": self.theory_diff,
            "theory_displacement": self.theory_displacement,
            "k_value": self.k_value,
            "daily_liquid": self.daily_liquid,
            "daily_oil": self.daily_oil,
            "production_time": self.production_time,
            "total_oil": self.total_oil,
        }