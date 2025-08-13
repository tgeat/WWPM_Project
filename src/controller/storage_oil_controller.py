import re
import uuid
from typing import Optional

import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QApplication, QMessageBox, QPushButton,
                             QAbstractItemView, QRadioButton, QWidget, QHBoxLayout)
from datetime import date, datetime, timedelta
import sys
import pickle
import os
import logging
from src.view.storage_oil_view import OilStorageView
from src.model.storage_oil_model import OilWellModel, ReportData
from src.database.oil_report_dao import MySQLManager
from src.database.water_report_dao import list_root, list_children, find_by_sequence


# 数据持久化工具类，保持在本地一天
class DataPersistence:
    """用于保存和加载当天数据，确保程序重启后同一天数据不丢失"""

    def __init__(self, save_path="oil_well_data.pkl"):
        self.save_path = save_path

    def save_data(self, reports, current_date):
        """保存数据及对应的日期"""
        try:
            data = {
                "date": current_date,
                "reports": reports
            }
            with open(self.save_path, "wb") as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"保存数据失败: {e}")
            return False

    def load_data(self):
        """加载数据，返回(数据列表, 保存日期)或(None, None)"""
        try:
            if not os.path.exists(self.save_path):
                return None, None

            with open(self.save_path, "rb") as f:
                data = pickle.load(f)
            return data["reports"], data["date"]
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None, None

    def delete_data(self):
        """删除保存的文件"""
        if os.path.exists(self.save_path):
            os.remove(self.save_path)

#从输入框获取到表格
class SimpleTableModel(QAbstractTableModel):
    def __init__(self, headers, rows, controller):
        super().__init__()
        self.headers = headers
        self.rows = rows  # 格式: [[平台, 井号, 日期, ..., id], ...]（id不显示）
        self.controller = controller

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.rows[index.row()][index.column()]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        """允许修改单元格数据并同步到数据源"""
        if role == Qt.EditRole and index.isValid():
            row = index.row()
            col = index.column()

            # 更新模型数据
            self.rows[row][col] = value
            self.dataChanged.emit(index, index)

            self.controller.sync_table_cell_change(row, col, value)
            return True
        return False

    def headerData(self, section, orient, role):
        if role == Qt.DisplayRole and orient == Qt.Horizontal:
            return self.headers[section] if 0 <= section < len(self.headers) else None
        return None

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def update_data(self, new_rows):
        """更新模型数据并通知视图刷新"""
        self.beginResetModel()
        self.rows = new_rows
        self.endResetModel()


# 是否单选框容器类，用于处理单选框状态变化
class RadioButtonWidget(QWidget):
    state_changed = pyqtSignal(int, str, str, bool)  # 行索引, 平台, 井号, 是否选中"是"

    def __init__(self, row_idx, platform, well_code, initial_state, parent=None):
        super().__init__(parent)
        self.row_idx = row_idx
        self.platform = platform
        self.well_code = well_code

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)

        self.radio_yes = QRadioButton("是")
        self.radio_no = QRadioButton("否")

        if initial_state == "是":
            self.radio_yes.setChecked(True)
        else:
            self.radio_no.setChecked(True)

        self.radio_yes.toggled.connect(self.on_state_changed)

        layout.addWidget(self.radio_yes)
        layout.addWidget(self.radio_no)
        self.setLayout(layout)

    def on_state_changed(self, checked):
        if checked:
            self.state_changed.emit(self.row_idx, self.platform, self.well_code, True)
        else:
            self.state_changed.emit(self.row_idx, self.platform, self.well_code, False)

#在后台线程中保存数据
class DbUpdateThread(QThread):
    result_signal = pyqtSignal(bool, str)

    def __init__(self, reports_data, index):
        super().__init__()
        self.reports_data = reports_data
        self.index = index

    def run(self):
        try:
            # 保存当前数据到本地文件
            DataPersistence().save_data(self.reports_data, date.today())
            self.result_signal.emit(True, "更新成功")
        except Exception as e:
            self.result_signal.emit(False, f"操作失败: {str(e)}")

#异步数据库操作线程，避免界面卡顿
class DbAsyncThread(QThread):
    result_signal = pyqtSignal(bool, str)

    def __init__(self, db_manager, action, reports_data=None):
        super().__init__()
        self.db_manager = db_manager
        self.action = action
        self.reports_data = reports_data

    def run(self):
        try:
            if self.action == 'sync':
                reports_dict = [report.to_dict() for report in self.reports_data]
                success, msg = self.db_manager.sync_to_backup(reports_dict)
            elif self.action == 'clear':
                success, msg = self.db_manager.clear_current_table()
            else:
                raise ValueError(f"未知操作类型: {self.action}")

            self.result_signal.emit(success, msg)
        except Exception as e:
            self.result_signal.emit(False, f"操作失败: {str(e)}")

#定时检查数据库中的公式是否有变更
class FormulaCheckThread(QThread):
    formula_changed = pyqtSignal()

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.last_formulas_hash = None
        self.running = True

    def run(self):
        while self.running:
            try:
                current_formulas = self.get_formulas()
                current_hash = hash(tuple(current_formulas))

                if self.last_formulas_hash is None:
                    self.last_formulas_hash = current_hash
                elif current_hash != self.last_formulas_hash:
                    self.last_formulas_hash = current_hash
                    self.formula_changed.emit()

                self.msleep(30000)  # 每30秒检查一次
            except Exception as e:
                print(f"公式检查线程错误: {e}")
                self.msleep(10000)

    def get_formulas(self):
        try:
            from sqlalchemy.orm import Session
            from src.database.db_oil_schema import FormulaData

            with Session(self.db_manager.engine) as session:
                records = session.query(FormulaData.formula).all()

            valid_formulas = []
            for record in records:
                formula_str = record[0] if (record and len(record) > 0) else None
                if isinstance(formula_str, str) and formula_str.strip():
                    valid_formulas.append(formula_str.strip())

            return valid_formulas
        except Exception as e:
            print(f"获取公式失败: {e}")
            return []

    def stop(self):
        self.running = False
        self.wait()

#公式溯源
class FormulaDependency:
    def __init__(self):
        self.field_formula_map = {}  # 字段名 -> 原始公式
        self.field_deps_map = {}  # 字段名 -> 依赖的原始输入字段

    def build_dependencies(self, formulas):
        self.field_formula_map.clear()
        self.field_deps_map.clear()

        for formula in formulas:
            if "=" not in formula:
                continue
            target_field, expr = formula.split("=", 1)
            target_field = target_field.strip()
            self.field_formula_map[target_field] = expr.strip()

        for field in self.field_formula_map:
            self._parse_dependencies(field, self.field_formula_map[field], set())

    def _parse_dependencies(self, field, expr, visited):
        if field in visited:
            return
        visited.add(field)

        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
        raw_input_vars = []
        for var in variables:
            if var in self.field_formula_map:
                self._parse_dependencies(var, self.field_formula_map[var], visited)
                expr = expr.replace(var, f"({self.field_formula_map[var]})")
            else:
                raw_input_vars.append(var)

        self.field_formula_map[field] = expr
        self.field_deps_map[field] = raw_input_vars


class OilStorageController:
    def __init__(self):
        self.view = OilStorageView()
        self.init_ui()
        self.db_manager = MySQLManager()
        self.data_persistence = DataPersistence()

        self.formulas = []
        self.formula_check_thread = None
        self.formula_deps = FormulaDependency()

        self.header_to_field = {
            "油压": "oil_pressure",
            "套压": "casing_pressure",
            "回压": "back_pressure",
            "合量斗数": "total_bucket",
            "时间标记": "time_sign",
            "憋压数据": "press_data",
            "生产时间": "prod_hours",
            "A2冲程": "a2_stroke",
            "A2冲次": "a2_frequency",
            "功图冲次": "work_stroke",
            "有效排液冲程": "effective_stroke",
            "充满系数": "fill_coeff_test",
            "化验含水": "lab_water_cut",
            "上报含水": "reported_water",
            "充满系数液量": "fill_coeff_liquid",
            "上次动管柱时间": "last_tubing_time",
            "泵径": "pump_diameter",
            "区块": "block",
            "变压器": "transformer",
            "备注": "remark",
            "井次": "well_times",
            "液量/斗数": "liquid_per_bucket",
            "和": "sum_value",
            "液量": "liquid1",
            "生产系数": "production_coeff",
            "A2 24h液量": "a2_24h_liquid",
            "液量（资料员）": "liquid2",
            "油量": "oil_volume",
            "波动范围": "fluctuation_range",
            "停产时间": "shutdown_time",
            "理论排量-液量差值": "theory_diff",
            "理论排量": "theory_displacement",
            "K值": "k_value",
            "日产液": "daily_liquid",
            "日产油": "daily_oil",
            "时间": "production_time",
            "产油": "total_oil"
        }

        # 添加防递归标志
        self.is_refreshing = False

        # 尝试加载本地保存的数据
        saved_reports, saved_date = self.data_persistence.load_data()
        today = date.today()

        # 判断是否是同一天数据
        if saved_reports and saved_date == today:
            self.current_reports = saved_reports
            for report in self.current_reports:
                if not hasattr(report, 'total_bucket_sign'):
                    report.total_bucket_sign = "是"
        else:
            self.current_reports = []  # 删除默认构造数据逻辑

        # 构建ID到报表的映射，提高查找效率
        self.report_id_map = {report.id: report for report in self.current_reports}
        self.current_record_id = None
        self.current_report_date = None
        self.radio_widgets = []

        # 设置定时器，每天凌晨更新日期并清空数据
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_and_update_daily)
        self.timer.start(3600000)


    def initialize(self):
        self.load_formulas()  # 加载公式
        self.creat_model_list()  # 构造日报数据模型
        self.calculate_all_reports()  # 使用公式计算所有报表字段
        self.creat_table()  # 创建表格模型并绑定
        self.load_history_data()  # 再次刷新视图
        self.bind_events()
        self.start_formula_check_thread()  # 启动后台线程监听公式变化

    def start_formula_check_thread(self):
        self.formula_check_thread = FormulaCheckThread(self.db_manager)
        self.formula_check_thread.formula_changed.connect(self.on_formula_changed)
        self.formula_check_thread.start()

    def on_formula_changed(self):
        if self.is_refreshing:
            return

        try:
            print("检测到公式更新，重新加载公式并计算数据")
            self.load_formulas()
            self.calculate_all_reports()
            self.load_history_data()
        except Exception as e:
            QMessageBox.critical(self.view, "公式更新错误", f"公式更新失败: {str(e)}")

    def load_formulas(self):
        try:
            from sqlalchemy.orm import Session
            from src.database.db_oil_schema import FormulaData

            with Session(self.db_manager.engine) as session:
                records = session.query(FormulaData.formula).all()

            field_mapping = {
                "油压": "oil_pressure",
                "套压": "casing_pressure",
                "回压": "back_pressure",
                "合量斗数": "total_bucket",
                "时间标记": "time_sign",
                "憋压数据": "press_data",
                "生产时间": "prod_hours",
                "A2冲程": "a2_stroke",
                "A2冲次": "a2_frequency",
                "功图冲次": "work_stroke",
                "有效排液冲程": "effective_stroke",
                "充满系数": "fill_coeff_test",
                "化验含水": "lab_water_cut",
                "上报含水": "reported_water",
                "充满系数液量": "fill_coeff_liquid",
                "上次动管柱时间": "last_tubing_time",
                "泵径": "pump_diameter",
                "区块": "block",
                "变压器": "transformer",
                "备注": "remark",
                "井次":"well_times",
                "液量/斗数": "liquid_per_bucket",
                "液量/斗数（功图）": "liquid_per_bucket",
                "液量/斗数（60/流量计）": "liquid_per_bucket1",
                "和": "sum_value",
                "液量": "liquid1",
                "生产系数": "production_coeff",
                "A2 24h液量": "a2_24h_liquid",
                "液量（资料员）": "liquid2",
                "油量": "oil_volume",
                "波动范围": "fluctuation_range",
                "停产时间": "shutdown_time",
                "理论排量-液量差值": "theory_diff",
                "理论排量": "theory_displacement",
                "K值": "k_value",
                "日产液": "daily_liquid",
                "日产油": "daily_oil",
                "时间": "production_time",
                "产油": "total_oil"
            }

            self.formulas = []
            for record in records:
                formula_str = record[0] if (record and len(record) > 0) else None
                if isinstance(formula_str, str) and formula_str.strip():
                    processed_formula = formula_str.strip()
                    # 替换字段映射，使用更高效的正则方式
                    for ch_field, en_field in field_mapping.items():
                        processed_formula = re.sub(rf"\b{re.escape(ch_field)}\b", en_field, processed_formula)
                    self.formulas.append(processed_formula)

            self.formula_deps.build_dependencies(self.formulas)
            print(f"加载公式成功，共 {len(self.formulas)} 条")
        except Exception as e:
            print(f"加载公式失败: {e}")
            self.formulas = []

    def calculate_all_reports(self):
        if not self.formulas or self.is_refreshing:
            print("没有可用的公式或正在刷新，跳过计算")
            return

        # 批量计算时使用循环，避免重复操作
        for report in self.current_reports:
            self.calculate_report(report)

        self.data_persistence.save_data(self.current_reports, date.today())
        self.load_history_data()

    def calculate_report(self, report):
        try:
            report_dict = report.__dict__
            numeric_fields = {}

            # 优化数值转换逻辑
            for field, value in report_dict.items():
                try:
                    numeric_fields[field] = float(value) if value and str(value).strip() else ""
                except (ValueError, TypeError):
                    numeric_fields[field] = value

            time_sign = report.time_sign
            liquid_per_bucket_value = ""

            if time_sign:
                formula_suffix = ""
                if time_sign == "功图":
                    formula_suffix = "（功图）"
                elif time_sign in ["60", "流量计"]:
                    formula_suffix = "（60/流量计）"

                formula_name = f"liquid_per_bucket{formula_suffix}"
                expr = self.formula_deps.field_formula_map.get(formula_name, "")

                if expr:
                    try:
                        deps = self.formula_deps.field_deps_map.get(formula_name, [])
                        # 优化依赖检查逻辑
                        missing_deps = []
                        for dep in deps:
                            dep_value = numeric_fields.get(dep, "")
                            if not dep_value or str(dep_value).strip() == "":
                                missing_deps.append(dep)

                        if not missing_deps:
                            # 使用更安全的表达式计算方式
                            result = eval(expr, {"__builtins__": None}, numeric_fields)
                            if isinstance(result, (int, float)):
                                liquid_per_bucket_value = str(round(result, 2))
                            else:
                                liquid_per_bucket_value = str(result)
                    except Exception as e:
                        print(f"液量/斗数计算失败: {e}，公式: {expr}")
                        liquid_per_bucket_value = ""

            report.liquid_per_bucket = liquid_per_bucket_value
            numeric_fields["liquid_per_bucket"] = liquid_per_bucket_value

            # 计算其他字段
            for field in self.formula_deps.field_formula_map:
                if field.startswith("liquid_per_bucket"):
                    continue

                expr = self.formula_deps.field_formula_map[field]
                deps = self.formula_deps.field_deps_map[field]

                # 快速检查是否有缺失依赖
                has_empty_dep = any(
                    not str(numeric_fields.get(dep, "")).strip()
                    for dep in deps
                )

                if has_empty_dep:
                    setattr(report, field, "")
                    continue

                try:
                    result = eval(expr, {"__builtins__": None}, numeric_fields)
                    if isinstance(result, (int, float)):
                        result = round(result, 2)
                    setattr(report, field, str(result))
                except Exception as e:
                    print(f"公式计算失败 [{field}]: {e}")
                    setattr(report, field, "")
        except Exception as e:
            print(f"计算报表失败: {e}")

    #返回界面视图对象
    def get_view(self):
        return self.view
    #拆分并保存权限信息
    def put_accout_info(self, permission: str):
        parts = permission.split("_")
        if len(parts) < 5:
            raise ValueError("权限字符串格式错误")
        self.permission_list = parts
        self.area_name = parts[1]
        self.team_name = parts[2]
        self.room_no = parts[3]
        self.report_type = parts[4]

    #主界面调用根据权限加载平台-井的模型列表
    def creat_model_list(self):
        self.current_reports = []
        today = date.today()
        logger = logging.getLogger()

        try:
            for area in list_root():
                if area.area_name == self.area_name:
                    area_id = area.area_id
                    logger.debug(f"匹配到作业区: {area.area_name}, ID={area_id}")

                    for team in list_children("area", area_id):
                        if team.team_name == self.team_name:
                            team_id = team.team_id
                            logger.debug(f"匹配到班组: {team.team_name}, ID={team_id}")

                            for room in list_children("team", team_id):
                                if room.room_no == self.room_no:
                                    room_id = room.id
                                    logger.debug(f"匹配到计量间: {room.room_no}, ID={room_id}")

                                    for bao in list_children("room", room_id):
                                        logger.debug(
                                            f"找到Bao: id={bao.id if hasattr(bao, 'bao_id') else getattr(bao, 'id', 'N/A')} 类型={getattr(bao, 'bao_typeid', '未知')}")
                                        if getattr(bao, 'bao_typeid', '') == "油报":
                                            for platform in list_children("bao", bao.id):
                                                logger.debug(
                                                    f"处理平台: id={platform.id} 编号={platform.platformer_id}")
                                                for well in list_children("platform", platform.id):
                                                    logger.debug(f"处理井: 井号={well.well_code} ID={well.id}")
                                                    try:
                                                        existing_report = find_by_sequence([
                                                            area_id,
                                                            team_id,
                                                            room_id,
                                                            bao.id,
                                                            platform.id,
                                                            well.id,
                                                            today
                                                        ])
                                                        if existing_report is None:
                                                            report = ReportData(platform.platformer_id, well.well_code)
                                                            report.create_time = today
                                                            report.id = f"{platform.platformer_id}_{well.well_code}_{today}"
                                                            logger.debug(f"新建日报数据: {report.id}")
                                                        else:
                                                            report = existing_report
                                                            logger.debug(f"已存在日报数据: {report.id}")
                                                        self.current_reports.append(report)
                                                    except Exception as e:
                                                        logger.error(f"处理井数据时出错: {well.well_code} 错误: {e}",
                                                                     exc_info=True)
        except Exception as e:
            logger.error(f"构建模型列表时出现错误: {e}", exc_info=True)

    #主界面调用构建油报表格
    def creat_table(self):
        headers = [
            "平台", "井号", "日期", "是否合量斗数", "合量斗数", "时间标记", "油压", "套压", "回压",
            "憋压数据", "生产时间", "A2冲程", "A2冲次", "功图冲次",
            "有效排液冲程", "充满系数", "化验含水", "上报含水",
            "充满系数液量", "上次动管柱时间", "泵径", "区块", "变压器", "备注", "井次",
            "每桶液量", "和", "液量1", "生产系数", "A2 24h液量", "液量2",
            "油量", "波动范围", "停产时间", "理论差值", "理论排量", "K值",
            "日产液", "日产油", "时间", "总产油"
        ]

        rows = []
        for report in self.current_reports:
            r = report.to_dict()
            row = [r.get(k, "") for k in [
                "platform", "well_code", "create_time", "total_bucket_sign", "total_bucket", "time_sign",
                "oil_pressure", "casing_pressure", "back_pressure", "press_data", "prod_hours",
                "a2_stroke", "a2_frequency", "work_stroke", "effective_stroke", "fill_coeff_test",
                "lab_water_cut", "reported_water", "fill_coeff_liquid", "last_tubing_time",
                "pump_diameter", "block", "transformer", "remark", "well_times", "liquid_per_bucket", "sum_value",
                "liquid1", "production_coeff", "a2_24h_liquid", "liquid2", "oil_volume",
                "fluctuation_range", "shutdown_time", "theory_diff", "theory_displacement",
                "k_value", "daily_liquid", "daily_oil", "production_time", "total_oil"
            ]]
            row.append(r.get("id", ""))
            rows.append(row)

        model = SimpleTableModel(headers, rows, self)
        self.view.ui.tableView.setModel(model)
        self.view.ui.tableView.horizontalHeader().setDefaultSectionSize(150)
        self.view.ui.tableView.verticalHeader().setDefaultSectionSize(60)

    #检查时间是否是新的一天
    def check_and_update_daily(self):
        """检查是否需要每日更新"""
        now = datetime.now()
        if now.hour == 0 and now.minute < 3:
            self.update_daily_data()
    #每天凌晨清空日报
    def update_daily_data(self):
        """每日更新：更新日期并清空除井号和平台外的字段"""
        today = date.today()
        for report in self.current_reports:
            report.create_time = today  # 更新到最新日期
            # 清空除井号和平台外的字段
            report.total_bucket_sign = "是"
            report.total_bucket = ""
            report.time_sign = ""
            report.oil_pressure = ""
            report.casing_pressure = ""
            report.back_pressure = ""
            report.press_data = ""
            report.prod_hours = ""
            report.a2_stroke = ""
            report.a2_frequency = ""
            report.work_stroke = ""
            report.effective_stroke = ""
            report.fill_coeff_test = ""
            report.lab_water_cut = ""
            report.reported_water = ""
            report.fill_coeff_liquid = ""
            report.last_tubing_time = ""
            report.pump_diameter = ""
            report.block = ""
            report.transformer = ""
            report.remark = ""
            report.liquid_per_bucket = ""
            report.sum_value = ""
            report.liquid1 = ""
            report.production_coeff = ""
            report.a2_24h_liquid = ""
            report.liquid2 = ""
            report.oil_volume = ""
            report.fluctuation_range = ""
            report.shutdown_time = ""
            report.theory_diff = ""
            report.theory_displacement = ""
            report.k_value = ""
            report.daily_liquid = ""
            report.daily_oil = ""
            report.well_times = ""
            report.production_time = ""
            report.total_oil = ""

        # 保存更新后的数据
        self.data_persistence.save_data(self.current_reports, today)

        # 重新加载数据显示
        self.load_history_data()
        QMessageBox.information(self.view, "每日更新", "已自动更新日期并清空数据")

    #设置表格和按钮
    def init_ui(self):
        tableView = self.view.ui.tableView
        tableView.setSelectionBehavior(QAbstractItemView.SelectItems)
        tableView.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.NoEditTriggers)
        tableView.setAlternatingRowColors(True)
        tableView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        tableView.setContextMenuPolicy(Qt.CustomContextMenu)

        self.view.ui.pushButton_3.setEnabled(False)
        self.view.ui.pushButton_4.setEnabled(False)
        self.clear_fields()
    #事件绑定
    def bind_events(self):
        self.view.get_calculate_button().clicked.connect(self.calculate_and_display)
        self.view.get_input_submit_button().clicked.connect(self.submit_data)
        self.view.get_result_submit_button().clicked.connect(self.submit_data)
        self.view.ui.pushButton_2.clicked.connect(self.update_daily_data)
        self.view.ui.tableView.customContextMenuRequested.connect(self.show_context_menu)
        self.view.ui.pushButton.clicked.connect(self.sync_all_data)
        self.view.ui.pushButton_4.clicked.connect(self.load_previous_day_report)
        self.view.ui.pushButton_add.clicked.connect(self.view.zoom_in)
        self.view.ui.pushButton_minus.clicked.connect(self.view.zoom_out)

    def calculate_and_display(self):
        try:
            current_report = self._get_current_editing_report()
            if not current_report:
                QMessageBox.warning(self.view, "警告", "请先选择报表并填写数据")
                return

            self._update_report_from_input(current_report)
            self.calculate_report(current_report)
            self._display_report_to_result_page(current_report)

            QMessageBox.information(self.view, "计算完成", "数据计算已完成，即将切换到结果页面")
            if hasattr(self.view.ui, 'tabWidget'):
                self.view.ui.tabWidget.setCurrentIndex(1)
            else:
                print("未找到tabWidget，无法自动切换页面")
        except Exception as e:
            QMessageBox.critical(self.view, "计算错误", f"计算失败: {str(e)}")

    def _get_current_editing_report(self) -> Optional[ReportData]:
        well_code = self.view.get_lineEdit_wellNum().text()
        platform = self.view.get_lineEdit_injectFuc().text()
        if not well_code or not platform:
            return None

        for r in self.current_reports:
            if r.well_code == well_code and r.platform == platform:
                return r

            # 报表不存在，创建新报表
        new_report = ReportData(platform=platform, well_code=well_code)
        new_report.total_bucket_sign = "是"
        new_report.id = str(uuid.uuid4())  # 保证唯一性

        self.current_reports.append(new_report)
        self.report_id_map[new_report.id] = new_report
        return new_report

    def _update_report_from_input(self, report: ReportData):
        """从tab1输入控件更新报表的输入数据"""
        model = OilWellModel.from_view(self.view)
        # 输入数据字段更新
        report.oil_pressure = model.oil_pressure
        report.casing_pressure = model.casing_pressure
        report.back_pressure = model.back_pressure
        report.total_bucket = model.total_bucket
        report.time_sign = model.time_sign
        report.press_data = model.press_data
        report.prod_hours = model.prod_hours
        report.a2_stroke = model.a2_stroke
        report.a2_frequency = model.a2_frequency
        report.work_stroke = model.work_stroke
        report.effective_stroke = model.effective_stroke
        report.fill_coeff_test = model.fill_coeff_test
        report.lab_water_cut = model.lab_water_cut
        report.reported_water = model.reported_water
        report.fill_coeff_liquid = model.fill_coeff_liquid
        report.last_tubing_time = model.last_tubing_time
        report.pump_diameter = model.pump_diameter
        report.block = model.block
        report.transformer = model.transformer
        report.remark = model.remark
        report.well_times = model.well_times

    def _display_report_to_result_page(self, report: ReportData):
        """将报表的计算结果显示到tab2控件"""
        if not report:
            return

        self.view.get_lineEdit_liquid_bucket().setText(report.liquid_per_bucket)
        self.view.get_lineEdit_sum().setText(report.sum_value)
        self.view.get_lineEdit_liquid().setText(report.liquid1)
        self.view.get_lineEdit_distribution_coeff().setText(report.production_coeff)
        self.view.get_lineEdit_a2_24h().setText(report.a2_24h_liquid)
        self.view.get_lineEdit_liquid_data().setText(report.liquid2)
        self.view.get_lineEdit_oil().setText(report.oil_volume)
        self.view.get_lineEdit_fluctuation_range().setText(report.fluctuation_range)
        self.view.get_lineEdit_stop_time().setText(report.shutdown_time)
        self.view.get_lineEdit_theory_diff().setText(report.theory_diff)
        self.view.get_lineEdit_theory_displacement().setText(report.theory_displacement)
        self.view.get_lineEdit_k_value().setText(report.k_value)
        self.view.get_lineEdit_daily_liquid().setText(report.daily_liquid)
        self.view.get_lineEdit_daily_oil().setText(report.daily_oil)
        self.view.get_lineEdit_time().setText(report.production_time)
        self.view.get_lineEdit_produce_oil().setText(report.total_oil)
    #加载前一天的日报记录
    def load_previous_day_report(self):
        try:
            if not self.current_record_id:
                QMessageBox.warning(self.view, "警告", "请先选择要修改的报表！")
                return

            # 使用映射快速查找报表
            current_report = self.report_id_map.get(self.current_record_id)
            if not current_report:
                QMessageBox.warning(self.view, "警告", "未找到当前记录！")
                return

            platform = current_report.platform
            well_code = current_report.well_code
            current_date = current_report.create_time

            previous_data = self.db_manager.fetch_previous_day_report(well_code, platform, current_date)
            if not previous_data:
                QMessageBox.information(self.view, "提示",
                                        f"未查询到 {platform}-{well_code} 在 {current_date - timedelta(days=1)} 的数据")
                return

            oil_well_model = OilWellModel.from_db_record(previous_data)
            oil_well_model.to_view(self.view)  # 同时更新tab1和tab2
            self.view.get_lineEdit_wellNum().setText(well_code)
            self.view.get_lineEdit_injectFuc().setText(platform)

            QMessageBox.information(self.view, "成功",
                                    f"已加载 {current_date - timedelta(days=1)} 的历史数据")
        except Exception as e:
            QMessageBox.warning(self.view, "错误", f"加载失败: {str(e)}")
    #将表格中的数据上报到数据库
    def sync_all_data(self):
        reply = QMessageBox.question(
            self.view, "确认上报",
            "即将将当前表数据上报到历史报表，是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.view.ui.pushButton.setEnabled(False)
            self.db_thread = DbAsyncThread(self.db_manager, 'sync', self.current_reports)
            self.db_thread.result_signal.connect(self.handle_sync_result)
            self.db_thread.start()
    #上报结果处理器
    def handle_sync_result(self, success, msg):
        self.view.ui.pushButton.setEnabled(True)
        if success:
            QMessageBox.information(self.view, "成功", msg)
            self.load_history_data()
        else:
            QMessageBox.warning(self.view, "失败", msg)
    #清空所有日报数据（保留井号和平台）
    def clear_all_data(self):
        reply = QMessageBox.question(
            self.view, "警告",
            "确认清空当前报表数据（保留井号和平台）？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # 清空除井号和平台外的所有字段
            today = date.today()
            for report in self.current_reports:
                report.create_time = today
                report.total_bucket_sign = "是"
                report.total_bucket = ""
                report.time_sign = ""
                report.oil_pressure = ""
                report.casing_pressure = ""
                report.back_pressure = ""
                report.press_data = ""
                report.prod_hours = ""
                report.a2_stroke = ""
                report.a2_frequency = ""
                report.work_stroke = ""
                report.effective_stroke = ""
                report.fill_coeff_test = ""
                report.lab_water_cut = ""
                report.reported_water = ""
                report.fill_coeff_liquid = ""
                report.last_tubing_time = ""
                report.pump_diameter = ""
                report.block = ""
                report.transformer = ""
                report.remark = ""

            # 保存清空后的数据
            self.data_persistence.save_data(self.current_reports, today)
            self.load_history_data()
            QMessageBox.information(self.view, "成功", "当前报表数据已清空")
    #清空单条数据的处理反馈
    def handle_clear_result(self, success, msg):
        self.view.ui.pushButton_2.setEnabled(True)
        if success:
            QMessageBox.information(self.view, "成功", msg)
            self.clear_fields()
            self.load_history_data()
        else:
            QMessageBox.warning(self.view, "失败", msg)
    #清空表单字段
    def clear_fields(self):
        fields = [
            self.view.get_lineEdit_wellNum(),
            self.view.get_lineEdit_injectFuc(),
            self.view.get_lineEdit_oilPres(),
            self.view.get_lineEdit_casePres(),
            self.view.get_lineEdit_wellOilPres(),
            self.view.get_lineEdit_firstExecl(),
            self.view.get_lineEdit_10(),
            self.view.get_lineEdit_firstWater(),
            self.view.get_lineEdit_productLong(),
            self.view.get_lineEdit_mainLinePres(),
            self.view.get_lineEdit_2(),
            self.view.get_lineEdit_daliyWater(),
            self.view.get_lineEdit_totalWater(),
            self.view.get_lineEdit_3(),
            self.view.get_lineEdit_testWater(),
            self.view.get_lineEdit_4(),
            self.view.get_lineEdit_5(),
            self.view.get_lineEdit_6(),
            self.view.get_lineEdit_7(),
            self.view.get_lineEdit_8(),
            self.view.get_lineEdit_9(),
            self.view.get_lineEdit_note(),
            self.view.get_lineEdit_nums(),
            # tab2结果控件
            self.view.get_lineEdit_liquid_bucket(),
            self.view.get_lineEdit_sum(),
            self.view.get_lineEdit_liquid(),
            self.view.get_lineEdit_distribution_coeff(),
            self.view.get_lineEdit_a2_24h(),
            self.view.get_lineEdit_liquid_data(),
            self.view.get_lineEdit_oil(),
            self.view.get_lineEdit_fluctuation_range(),
            self.view.get_lineEdit_stop_time(),
            self.view.get_lineEdit_theory_diff(),
            self.view.get_lineEdit_theory_displacement(),
            self.view.get_lineEdit_k_value(),
            self.view.get_lineEdit_daily_liquid(),
            self.view.get_lineEdit_daily_oil(),
            self.view.get_lineEdit_time(),
            self.view.get_lineEdit_produce_oil()
        ]
        for le in fields:
            le.clear()
            le.setEnabled(True)

        self.view.get_input_submit_button().setEnabled(False)
        self.view.get_result_submit_button().setEnabled(False)
        self.current_record_id = None
        self.current_report_date = None
    #提交按钮事件
    def submit_data(self):
        """合并后的提交按钮处理方法，更新两个tab的数据并处理合量斗数逻辑"""
        if self.is_refreshing:
            return

        try:
            if not self.current_record_id:
                QMessageBox.warning(self.view, "警告", "请先选择要修改的报表！")
                return

            model = self.collect_ui_data()
            if not model.well_code or not model.platform:
                QMessageBox.warning(self.view, "警告", "井组和平台为必填项！")
                return

            current_report = self.report_id_map.get(self.current_record_id)
            if not current_report:
                QMessageBox.warning(self.view, "警告", "未找到当前编辑的报表数据")
                return

            self._update_report_from_input(current_report)
            self._update_report_from_result_page(current_report)

            total_bucket_sign = current_report.total_bucket_sign  # 保持原状态

            if total_bucket_sign == "是":
                platform = model.platform
                target_bucket = model.total_bucket
                for report in self.current_reports:
                    if report.platform == platform and report.total_bucket_sign == "是":
                        report.total_bucket = target_bucket

            self.data_persistence.save_data(self.current_reports, date.today())

            self.report_id_map = {report.id: report for report in self.current_reports}
            self.load_history_data()
            self.clear_fields()

            QMessageBox.information(self.view, "成功", "数据已更新！")
        except Exception as e:
            QMessageBox.critical(self.view, "提交错误", f"提交失败: {str(e)}")
        finally:
            self.is_refreshing = False

    def _update_report_from_result_page(self, report: ReportData):
        """从tab2结果控件更新报表的计算结果数据"""
        report.liquid_per_bucket = self.view.get_lineEdit_liquid_bucket().text()
        report.sum_value = self.view.get_lineEdit_sum().text()
        report.liquid1 = self.view.get_lineEdit_liquid().text()
        report.production_coeff = self.view.get_lineEdit_distribution_coeff().text()
        report.a2_24h_liquid = self.view.get_lineEdit_a2_24h().text()
        report.liquid2 = self.view.get_lineEdit_liquid_data().text()
        report.oil_volume = self.view.get_lineEdit_oil().text()
        report.fluctuation_range = self.view.get_lineEdit_fluctuation_range().text()
        report.shutdown_time = self.view.get_lineEdit_stop_time().text()
        report.theory_diff = self.view.get_lineEdit_theory_diff().text()
        report.theory_displacement = self.view.get_lineEdit_theory_displacement().text()
        report.k_value = self.view.get_lineEdit_k_value().text()
        report.daily_liquid = self.view.get_lineEdit_daily_liquid().text()
        report.daily_oil = self.view.get_lineEdit_daily_oil().text()
        report.production_time = self.view.get_lineEdit_time().text()
        report.total_oil = self.view.get_lineEdit_produce_oil().text()
    # 加载内存中的历史数据并渲染表格视图
    def load_history_data(self):
        if self.is_refreshing:
            return

        try:
            self.is_refreshing = True
            tableView = self.view.ui.tableView
            tableView.clearSpans()

            for widget in self.radio_widgets:
                try:
                    widget.state_changed.disconnect()
                except:
                    pass
            self.radio_widgets.clear()

            rows = [report.to_dict() for report in self.current_reports]
            headers = [
                "平台", "井号", "日期", "是否合量斗数", "合量斗数", "时间标记", "油压", "套压", "回压",
                "憋压数据", "生产时间", "A2冲程", "A2冲次", "功图冲次",
                "有效排液冲程", "充满系数", "化验含水", "上报含水",
                "充满系数液量", "上次动管柱时间", "泵径", "区块", "变压器", "备注", "井次",
                "液量/斗数", "和", "液量", "生产系数", "A2 24h液量", "液量（资料员）",
                "油量", "波动范围", "停产时间", "理论排量-液量差值", "理论排量", "K值",
                "日产液", "日产油", "时间", "产油"
            ]

            table_rows = []
            grouped_data = {}
            for row in rows:
                platform = row.get("platform", "")
                grouped_data.setdefault(platform, []).append(row)
            sorted_platforms = sorted(grouped_data.keys())
            current_row = 0
            platform_row_ranges = {}
            for platform in sorted_platforms:
                group_rows = grouped_data[platform]
                platform_row_count = len(group_rows)
                platform_row_ranges[platform] = (current_row, platform_row_count)
                for row in group_rows:
                    display_row = [
                        row.get("platform", ""),
                        row.get("well_code", ""),
                        str(row.get("create_time", "")),
                        row.get("total_bucket_sign", "是"),
                        row.get("total_bucket", ""),
                        row.get("time_sign", ""),
                        row.get("oil_pressure", ""),
                        row.get("casing_pressure", ""),
                        row.get("back_pressure", ""),
                        row.get("press_data", ""),
                        row.get("prod_hours", ""),
                        row.get("a2_stroke", ""),
                        row.get("a2_frequency", ""),
                        row.get("work_stroke", ""),
                        row.get("effective_stroke", ""),
                        row.get("fill_coeff_test", ""),
                        row.get("lab_water_cut", ""),
                        row.get("reported_water", ""),
                        row.get("fill_coeff_liquid", ""),
                        row.get("last_tubing_time", ""),
                        row.get("pump_diameter", ""),
                        row.get("block", ""),
                        row.get("transformer", ""),
                        row.get("remark", ""),
                        row.get("well_times",""),
                        row.get("liquid_per_bucket", ""),
                        row.get("sum_value", ""),
                        row.get("liquid1", ""),
                        row.get("production_coeff", ""),
                        row.get("a2_24h_liquid", ""),
                        row.get("liquid2", ""),
                        row.get("oil_volume", ""),
                        row.get("fluctuation_range", ""),
                        row.get("shutdown_time", ""),
                        row.get("theory_diff", ""),
                        row.get("theory_displacement", ""),
                        row.get("k_value", ""),
                        row.get("daily_liquid", ""),
                        row.get("daily_oil", ""),
                        row.get("production_time", ""),
                        row.get("total_oil", ""),
                        row.get("id", "")
                    ]
                    table_rows.append(display_row)
                    current_row += 1

            # 更新模型
            current_model = tableView.model()
            if current_model and isinstance(current_model, SimpleTableModel):
                current_model.update_data(table_rows)  # 调用强化后的更新方法
            else:
                current_model = SimpleTableModel(headers, table_rows, self)
                tableView.setModel(current_model)

            tableView.viewport().update()
            tableView.updateGeometry()

            for platform, (start_row, row_count) in platform_row_ranges.items():
                if row_count > 1:
                    tableView.setSpan(start_row, 0, row_count, 1)

            for row_idx in range(len(table_rows)):
                row_data = table_rows[row_idx]
                radio_widget = RadioButtonWidget(
                    row_idx=row_idx,
                    platform=row_data[0],
                    well_code=row_data[1],
                    initial_state=row_data[3]
                )
                radio_widget.state_changed.connect(self.on_radio_changed, Qt.QueuedConnection)
                tableView.setIndexWidget(current_model.index(row_idx, 3), radio_widget)
                self.radio_widgets.append(radio_widget)

            # 再次强制刷新
            tableView.viewport().repaint()

        except Exception as e:
            print(f"刷新表格异常：{str(e)}")  # 捕获并打印异常
            QMessageBox.critical(self.view, "刷新错误", f"表格刷新失败: {str(e)}")
        finally:
            self.is_refreshing = False

    def sync_table_cell_change(self, row_idx, col_idx, new_value):
        """将表格单元格修改同步到底层ReportData对象"""
        try:
            if col_idx in [0, 1, 2, 3]:
                return

            tableView = self.view.ui.tableView
            model = tableView.model()
            if not model or row_idx >= model.rowCount():
                return

            row_data = model.rows[row_idx]
            record_id = row_data[-1]  # 最后一列是记录ID
            if not record_id:
                print("未找到记录ID，无法同步数据")
                return

            report = self.report_id_map.get(record_id)
            if not report:
                print(f"未找到ID为{record_id}的报表数据")
                return

            headers = model.headers
            if col_idx >= len(headers):
                return

            header_name = headers[col_idx]
            field_name = self.header_to_field.get(header_name)
            if not field_name:
                print(f"未找到{header_name}对应的字段映射")
                return

            # 更新ReportData对象的字段值
            if hasattr(report, field_name):
                setattr(report, field_name, new_value)
                print(f"更新字段 {field_name} 为 {new_value}")

                self.data_persistence.save_data(self.current_reports, date.today())
                self.load_history_data()
            else:
                print(f"ReportData没有字段 {field_name}")

        except Exception as e:
            print(f"同步表格数据错误：{str(e)}")
            QMessageBox.warning(self.view, "同步错误", f"修改保存失败: {str(e)}")

    #查找表格中记录行位置
    def find_row_by_id(self, model, record_id):
        for row_idx in range(model.rowCount()):
            if model.rows[row_idx][-1] == record_id:
                return row_idx
        return -1
    #设置合量斗数
    def on_radio_changed(self, row_idx, platform, well_code, is_yes):
        if self.is_refreshing:
            return

        try:
            model = self.view.ui.tableView.model()
            if not model or row_idx >= model.rowCount():
                return

            record_id = model.rows[row_idx][-1]
            if not record_id:
                print("未找到记录ID")
                return

            new_value = "是" if is_yes else "否"

            report = self.report_id_map.get(record_id)
            if report:
                old_value = report.total_bucket_sign
                report.total_bucket_sign = new_value

                if new_value == "否":
                    report.total_bucket = ""
                # 同步同平台合量斗数
                elif new_value == "是":
                    same_platform_bucket = None
                    for r in self.current_reports:
                        if (r.platform == platform and r.total_bucket_sign == "是" and r.total_bucket):
                            same_platform_bucket = r.total_bucket
                            break
                    report.total_bucket = same_platform_bucket or ""

                self.calculate_report(report)

                self.data_persistence.save_data(self.current_reports, date.today())
                self.report_id_map = {r.id: r for r in self.current_reports}
                self.load_history_data()

                self.db_thread = DbUpdateThread(self.current_reports, row_idx)
                self.db_thread.result_signal.connect(
                    lambda success, err, p=platform: self.handle_radio_result(success, err, p)
                )
                self.db_thread.start()
        except Exception as e:
            QMessageBox.critical(self.view, "单选框错误", f"处理单选框变更失败: {str(e)}")

    #从指定行里面获取合量斗数
    def get_current_total_bucket(self, row_idx):
        model = self.view.ui.tableView.model()
        return model.rows[row_idx][4] if row_idx < model.rowCount() else ""

    def handle_radio_result(self, success, err, platform):
        if not success:
            print(f"单选框更新失败: {err}")
            return
    #修改报表
    def show_context_menu(self, pos):
        try:
            idx = self.view.ui.tableView.indexAt(pos)
            if idx.isValid():
                menu = QtWidgets.QMenu()
                menu.addAction("修改报表", lambda: self.populate_form_data(idx.row()))
                menu.exec_(self.view.ui.tableView.viewport().mapToGlobal(pos))
        except Exception as e:
            QMessageBox.critical(self.view, "菜单错误", f"显示右键菜单失败: {str(e)}")

    def collect_ui_data(self) -> OilWellModel:
        return OilWellModel.from_view(self.view)
    #修改报表功能
    def populate_form_data(self, row_index):
        """右键修改时，将表格数据回显到两个tab（优化版）"""
        try:
            table_model = self.view.ui.tableView.model()
            if not table_model or not (0 <= row_index < table_model.rowCount()):
                return

            row_data = table_model.rows[row_index]
            self.current_record_id = row_data[-1]
            self.current_report_date = row_data[2]

            db_record = {
                "well_code": row_data[1],
                "platform": row_data[0],
                "oil_pressure": row_data[6],
                "casing_pressure": row_data[7],
                "back_pressure": row_data[8],
                "total_bucket": row_data[4],
                "time_sign": row_data[5],
                "press_data": row_data[9],
                "prod_hours": row_data[10],
                "a2_stroke": row_data[11],
                "a2_frequency": row_data[12],
                "work_stroke": row_data[13],
                "effective_stroke": row_data[14],
                "fill_coeff_test": row_data[15],
                "lab_water_cut": row_data[16],
                "reported_water": row_data[17],
                "fill_coeff_liquid": row_data[18],
                "last_tubing_time": row_data[19],
                "pump_diameter": row_data[20],
                "block": row_data[21],
                "transformer": row_data[22],
                "remark": row_data[23],
                "well_times": row_data[24],  # 改动！！
                "total_bucket_sign": row_data[3],
                "liquid_per_bucket": row_data[25],
                "sum_value": row_data[26],
                "liquid1": row_data[27],
                "production_coeff": row_data[28],
                "a2_24h_liquid": row_data[29],
                "liquid2": row_data[30],
                "oil_volume": row_data[31],
                "fluctuation_range": row_data[32],
                "shutdown_time": row_data[33],
                "theory_diff": row_data[34],
                "theory_displacement": row_data[35],
                "k_value": row_data[36],
                "daily_liquid": row_data[37],
                "daily_oil": row_data[38],
                "production_time": row_data[39],
                "total_oil": row_data[40],
                "id": self.current_record_id
            }

            oil_well_model = OilWellModel.from_db_record(db_record)
            oil_well_model.to_view(self.view)

            current_report = self.report_id_map.get(self.current_record_id)
            if current_report:
                self._display_report_to_result_page(current_report)

            self.view.get_lineEdit_wellNum().setEnabled(False)
            self.view.get_lineEdit_injectFuc().setEnabled(False)
            self.view.get_input_submit_button().setEnabled(True)
            self.view.get_result_submit_button().setEnabled(True)
            self.view.ui.pushButton_4.setEnabled(True)


        except Exception as e:
            QMessageBox.warning(self.view, "操作失败", f"加载数据时出错: {str(e)}")
            print(f"populate_form_data错误: {e}")

    def show(self):
        self.view.show()

    def __del__(self):
        if self.formula_check_thread and self.formula_check_thread.isRunning():
            self.formula_check_thread.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = OilStorageController()
    controller.show()
    sys.exit(app.exec_())