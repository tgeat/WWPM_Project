# storage_controller.py
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout
from PyQt5 import QtWidgets
from datetime import datetime, date,timedelta # 根据你实际用到的名字来选
from decimal import Decimal
from PyQt5.QtWidgets import QSizePolicy

from database.db_schema import Bao
from view.storage_view import StorageView
from model.storage_model import StorageModel
from database.water_report_dao import (
    upsert_well, upsert_daily_report,
    upsert_meter_room, upsert_prod_team,
    upsert_work_area, list_children, list_root, find_by_sequence, upsert_water_well, DBSession)

class SimpleTableModel(QAbstractTableModel):
    def __init__(self, headers, rows):
        super().__init__()
        self.headers = headers
        self.rows = rows


    def rowCount(self, parent=QModelIndex()): return len(self.rows)
    def columnCount(self, parent=QModelIndex()): return len(self.headers)
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.rows[index.row()][index.column()]

    def headerData(self, section, orient, role):
        if role == Qt.DisplayRole and orient == Qt.Horizontal:
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return None


class StorageController:
    def __init__(self):
        # ---- 视图 ----
        self.view = StorageView()


        now_str = datetime.now().strftime("%Y-%m-%d")
        # 2. 设置到 lineEdit
        self.view.ui.label_17.setText(now_str+"水报")
        self.view.ui.label_17.setMaximumHeight(80)



        self.view.ui.lineEdit_wellNum.setReadOnly(True)
        self.view.ui.lineEdit_firstWater.setReadOnly(True)
        self.view.ui.lineEdit_secondWater.setReadOnly(True)
        self.view.ui.lineEdit_thirdWater.setReadOnly(True)

        # —— 新增：允许 tableView 自定义右键菜单 ——
        tv = self.view.ui.tableView
        tv.setContextMenuPolicy(Qt.CustomContextMenu)
        tv.customContextMenuRequested.connect(self._on_table_context_menu)


        # ---- 数据模型 ----
        self.model = StorageModel()

        self.model_list=[]

        self.report_list_yesterday=[]

        self.current_well_yesterday_report = None


        self.yesterday: date = date.today() - timedelta(days=1)

        font = self.view.ui.scrollAreaWidgetContents.font()
        font.setPointSize(30)
        self.view.ui.scrollAreaWidgetContents.setFont(font)

        for button in self.view.findChildren(QPushButton):
            font = button.font()
            font.setPointSize(30)
            button.setFont(font)

        self.current_size = self.view.ui.scrollAreaWidgetContents.font().pointSize()

        self.view.ui.pushButton_add.clicked.connect(lambda: self._change_font(+1))
        self.view.ui.pushButton_minus.clicked.connect(lambda: self._change_font(-1))
        self.view.ui.pushButton_3.clicked.connect(lambda:self.on_clicked_save())
        self.view.ui.pushButton.clicked.connect(lambda:self.save_to_db())
        self.view.ui.pushButton_4.clicked.connect(lambda:self.on_clicked_history())

        self.view.ui.lineEdit_firstExecl.textChanged.connect(self._on_first_changed)
        self.view.ui.lineEdit_secondExecl.textChanged.connect(self._on_second_changed)
        self.view.ui.lineEdit_thirdExcel.textChanged.connect(self._on_third_changed)

    def _on_first_changed(self,txt: str):
        if self.current_well_yesterday_report is None:
            # 可以清空一下输出框，或者直接 return
            self.view.ui.lineEdit_firstWater.clear()
            return
        if txt=="":
            return
        self.view.ui.lineEdit_firstWater.setText(str(Decimal(txt)-self.current_well_yesterday_report.meter_stage1))

    def _on_second_changed(self,txt: str):
        if self.current_well_yesterday_report is None:
            # 可以清空一下输出框，或者直接 return
            self.view.ui.lineEdit_firstWater.clear()
            return
        if txt=="":
            return
        self.view.ui.lineEdit_secondWater.setText(str(Decimal(txt)-self.current_well_yesterday_report.meter_stage2))

    def _on_third_changed(self,txt: str):
        if self.current_well_yesterday_report is None:
            # 可以清空一下输出框，或者直接 return
            self.view.ui.lineEdit_firstWater.clear()
            return
        if txt=="":
            return
        self.view.ui.lineEdit_thirdWater.setText(str(Decimal(txt)-self.current_well_yesterday_report.meter_stage3))


    def on_clicked_history(self):
        if self.current_well_yesterday_report is None:
            return
        self.view.get_lineEdit_injectFuc().setText(str(self.current_well_yesterday_report.injection_mode))
        self.view.get_lineEdit_productLong().setText(str(self.current_well_yesterday_report.prod_hours))
        self.view.get_lineEdit_mainLinePres().setText(str(self.current_well_yesterday_report.trunk_pressure))
        self.view.get_lineEdit_oilPres().setText(str(self.current_well_yesterday_report.oil_pressure))
        self.view.get_lineEdit_casePres().setText(str(self.current_well_yesterday_report.casing_pressure))
        self.view.get_lineEdit_wellOilPres().setText(str(self.current_well_yesterday_report.wellhead_pressure))
        self.view.get_lineEdit_daliyWater().setText(str(self.current_well_yesterday_report.plan_inject))
        self.view.get_lineEdit_firstExecl().setText(str(self.current_well_yesterday_report.meter_stage1))
        self.view.get_lineEdit_secondExecl().setText(str(self.current_well_yesterday_report.meter_stage2))
        self.view.get_lineEdit_thirdExcel().setText(str(self.current_well_yesterday_report.meter_stage3))
        self.view.get_lineEdit_totalWater().setText(str(self.current_well_yesterday_report.actual_inject))
        self.view.get_lineEdit_note().setText(str(self.current_well_yesterday_report.remark))


    def _on_table_context_menu(self, pos):

        tv = self.view.ui.tableView
        idx = tv.indexAt(pos)
        if not idx.isValid():
            return
        menu = QtWidgets.QMenu()
        modify = menu.addAction("修改报表")
        # 在视图坐标系映射到全局
        action = menu.exec_(tv.viewport().mapToGlobal(pos))
        if action == modify:
            self._modify_report(idx.row())

    # —— 新增：把 model_list[row] 的数据写回到各个 lineEdit ——
    def _modify_report(self, row: int):
        # 1）取出对应的 StorageModel
        m = self.model_list[row]
        self.current_well_yesterday_report=self.report_list_yesterday[row]
        # 2）设为当前 model（这样 load_from_model 可以复用）
        self.model = m
        # 3）把它写回界面
        #    假设 StorageModel 定义了 to_view(view) 方法：

        self.model.to_view(self.view)
        #    —— 或者直接调用已有的 load_from_model()：
        # self.load_from_model()


    def on_clicked_save(self):
        self.save_to_model()
        self.creat_table()

    def get_view(self):
        return self.view

    def creat_model_list(self):
        self.model_list = []
        today = date.today()
        self.report_list_yesterday = []

        # 根据权限列表解析区域信息
        for area in list_root():
            if area.area_name == self.permission_list[1]:
                self.area_id = area.area_id
                for team in list_children("area", self.area_id):
                    if team.team_name == self.permission_list[2]:
                        self.team_id = team.team_id
                        for room in list_children("team", self.team_id):
                            if room.room_no == self.permission_list[3]:
                                self.room_id = room.id

        # 找到计量间后，取其所有Bao，筛选“水报”
        bao_list = list_children("room", self.room_id)
        water_bao = [b for b in bao_list if b.bao_typeid == "水报"]
        if not water_bao:
            return

        # 取第一个水报Bao，遍历其所有井
        wells = list_children("bao", water_bao[0].id)
        for well in wells:
            model = StorageModel()
            model.wellNum = well.well_code

            r = find_by_sequence([self.area_id, self.team_id, self.room_id, well.id, today])
            if r is not None:
                model.injectFuc = r.injection_mode
                model.productLong = r.prod_hours
                model.mainLinePres = r.trunk_pressure
                model.oilPres = r.oil_pressure
                model.casePres = r.casing_pressure
                model.wellOilPres = r.wellhead_pressure
                model.daliyWater = r.plan_inject
                model.firstExecl = r.meter_stage1
                model.secondExecl = r.meter_stage2
                model.thirdExcel = r.meter_stage3
                model.totalWater = r.actual_inject
                model.note = r.remark

            self.model_list.append(model)
            self.report_list_yesterday.append(
                find_by_sequence([self.area_id, self.team_id, self.room_id, well.id, self.yesterday]))

    def creat_table(self):


        def _fmt(value):
            """兼容旧版 Python 的通用格式化函数"""
            if value is None:
                return ""
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(value, date):
                return value.strftime("%Y-%m-%d")
            if isinstance(value, Decimal):
                value = float(value)
            if isinstance(value, float):
                return f"{value:.2f}"
            return str(value)

        headers = [
            "井号","日期", "注水方式", "生产时长(h)",
            "干线压(MPa)", "油压(MPa)", "套压(MPa)", "井口压(MPa)",
            "计划注水(m³)", "实际注水(m³)", "备注",
            "计量阶段1", "计量阶段2", "计量阶段3"
        ]

        # 3) 把每条日报转成行数据
        rows = [
            (
                _fmt(m.wellNum), _fmt(date.today()), _fmt(m.injectFuc),
                _fmt(m.productLong), _fmt(m.mainLinePres), _fmt(m.oilPres),
                _fmt(m.casePres), _fmt(m.wellOilPres), _fmt(m.daliyWater),
                _fmt(m.totalWater),_fmt(m.note),
                _fmt(m.firstExecl), _fmt(m.secondExecl), _fmt(m.thirdExcel)
            )
            for m in self.model_list
        ]
        self.view.ui.tableView.setModel(SimpleTableModel(headers,rows))

    def put_accout_info(self, permission):
        parts = permission.split("_")
        if len(parts) >= 5:
            self.permission_list = parts[:4]
        else:
            self.permission_list = parts

    # ---------- 保存：界面 → Model ----------
    def save_to_model(self):
        self.model = StorageModel.from_view(self.view)
        print("已存入模型：", self.model.to_dict())
        for idx, m in enumerate(self.model_list):
            if m.wellNum == self.model.wellNum:
                self.model_list[idx] = self.model
                break

    def save_to_db(self):
        def to_int_or_none(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return None

        def to_float_or_none(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        for model in self.model_list:
            # 1. 逐级确保外键存在
            area_id = upsert_work_area(self.permission_list[1])
            teams = list_children("area", self.permission_list[1])
            for t in teams:
                if self.permission_list[2] == t.team_name:
                    self.team_no = t.team_no
            team_id = upsert_prod_team(area_id, self.team_no, team_name=self.permission_list[2])
            room_id = upsert_meter_room(team_id, room_no=self.permission_list[3], is_injection=False)

            # 通过 room_id 查找对应的 bao_id（水报ID）
            with DBSession() as db:
                bao = db.query(Bao).filter(Bao.room_id == room_id).first()
                if not bao:
                    raise ValueError(f"找不到对应的水报bao，room_id={room_id}")
                bao_id = bao.id

            # 使用 bao_id 调用水井接口
            well_id = upsert_water_well(bao_id, well_code=model.wellNum)

            # 2. 准备日报字典，带转换和空值处理
            rpt = dict(
                report_date=date.today(),
                injection_mode=model.injectFuc or None,
                prod_hours=to_int_or_none(model.productLong),
                trunk_pressure=to_float_or_none(model.mainLinePres),
                oil_pressure=to_float_or_none(model.oilPres),
                casing_pressure=to_float_or_none(model.casePres),
                wellhead_pressure=to_float_or_none(model.wellOilPres),
                plan_inject=to_float_or_none(model.daliyWater),
                actual_inject=to_float_or_none(model.totalWater),
                remark=model.note or None,
                meter_stage1=to_float_or_none(model.firstExecl),
                meter_stage2=to_float_or_none(model.secondExecl),
                meter_stage3=to_float_or_none(model.thirdExcel)
            )

            report_id = upsert_daily_report(well_id, rpt)
            print(f"日报已写入，report_id={report_id}")

    # ---------- 加载：Model → 界面 ----------
    def load_from_model(self):
        self.model.to_view(self.view)
        print("已写回界面")

    # ---------- 启动 ----------
    def show(self):
        self.view.show()

    def _change_font(self, delta: int):
        # 更新字号，最小为 1
        self.current_size = max(1, self.current_size + delta)

        # 遍历滚动区内容区的所有 QWidget 子控件（含 QTextEdit、QLabel、QLineEdit……）
        for widget in self.view.ui.scrollAreaWidgetContents.findChildren(QtWidgets.QWidget):
            f = widget.font()
            f.setPointSize(self.current_size)
            widget.setFont(f)
        for button in self.view.findChildren(QtWidgets.QPushButton):
            f = button.font()
            f.setPointSize(self.current_size)
            f.setBold(False)  # 可选：加粗
            button.setFont(f)

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    ctl = StorageController()
    ctl.show()
    sys.exit(app.exec_())
