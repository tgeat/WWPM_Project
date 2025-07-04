import sys, warnings, pathlib
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTreeView, QTableView, QSplitter,QTreeWidget,
    QVBoxLayout, QToolBar, QAction, QMessageBox, QInputDialog,
    QDialog, QFormLayout, QLineEdit, QDateEdit, QSpinBox,
    QDoubleSpinBox, QTextEdit, QDialogButtonBox, QMenu,QComboBox,
    QFormLayout,QDialogButtonBox,QTreeWidgetItem,QFileDialog
)

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex,QDate
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from decimal import Decimal
from datetime import date, datetime

# 屏蔽 sip 警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 保证 src/ 在导入路径
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

from dataBase.water_report_dao import (
    list_root, list_children, delete_entity,upsert_daily_report
)

from dataBase.db_schema import DailyReport, SessionLocal

import pandas as pd


def fmt(value):
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

class DraggableTreeWidget(QTreeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        # 简单加个边框样式
        self.setStyleSheet("""
            QTreeView::item {
                border: 1px solid #ccc;
                padding: 4px;
                margin: 2px;
            }
            QTreeView::item:selected {
                background: #3874f2;
                color: white;
            }
        """)

    def dropEvent(self, event):
        target = self.itemAt(event.pos())
        sel = self.selectedItems()
        if len(sel)!=1 or target is None:
            event.ignore(); return
        dragged = sel[0]
        origP = dragged.parent()
        pos = self.dropIndicatorPosition()
        newP = target.parent() if pos!=QTreeWidget.OnItem else target
        # 顶级只能顶级拖，子级只能本父下拖
        if (origP is None and newP is None) or (origP is not None and newP==origP):
            super().dropEvent(event)
        else:
            event.ignore()

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出水报")
        self.resize(600, 400)

        form = QFormLayout()
        # —— 作业区下拉
        self.area_combo = QComboBox()
        for area in list_root():
            self.area_combo.addItem(area.area_name, area.area_id)
        form.addRow("选择作业区：", self.area_combo)

        # —— 班组下拉
        self.team_combo = QComboBox()
        form.addRow("选择班组：", self.team_combo)

        # —— 日期选择
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate().addDays(-1))
        form.addRow("选择日期：", self.date_edit)

        # —— 拖拽树
        self.tree = DraggableTreeWidget()
        self.tree.setHeaderLabel("计量间 → 井（拖拽调整顺序）")

        # —— 确认/取消
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_export)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(self.tree, 1)
        lay.addWidget(buttons)

        # 信号关联
        self.area_combo.currentIndexChanged.connect(self._reload_teams)
        self.team_combo.currentIndexChanged.connect(self._reload_tree)

        # 初始化
        self._reload_teams()

    def _reload_teams(self):
        """根据 area_combo 更新 team_combo"""
        self.team_combo.clear()
        area_id = self.area_combo.currentData()
        for team in list_children("area", area_id):
            self.team_combo.addItem(team.team_name, team.team_id)
        # 选完班组后，刷新树
        self._reload_tree()

    def _reload_tree(self):
        """根据 team_combo 填充左侧的可拖拽树"""
        self.tree.clear()
        team_id = self.team_combo.currentData()
        for room in list_children("team", team_id):
            room_item = QTreeWidgetItem([room.room_no])
            room_item.setFlags(room_item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            self.tree.addTopLevelItem(room_item)
            for well in list_children("room", room.room_id):
                well_item = QTreeWidgetItem([well.well_code])
                well_item.setFlags(well_item.flags() | Qt.ItemIsDragEnabled)
                room_item.addChild(well_item)
        self.tree.expandAll()

    def _gather_order(self):
        """读取当前树内用户排序"""
        order = []
        for i in range(self.tree.topLevelItemCount()):
            room_item = self.tree.topLevelItem(i)
            room_no = room_item.text(0)
            wells = [room_item.child(j).text(0) for j in range(room_item.childCount())]
            order.append((room_no, wells))
        return order

    def _on_export(self):
        team_id  = self.team_combo.currentData()
        team_txt = self.team_combo.currentText()
        rpt_date = self.date_edit.date().toPyDate()

        rows = []
        for room_no, wells in self._gather_order():
            room_obj = next(r for r in list_children("team", team_id) if r.room_no==room_no)
            for well_code in wells:
                well_obj = next(w for w in list_children("room", room_obj.room_id) if w.well_code==well_code)
                with SessionLocal() as db:
                    rpt = db.query(DailyReport).filter_by(
                        well_id     = well_obj.well_id,
                        report_date = rpt_date
                    ).first()
                if rpt:
                    rows.append({
                    "井号":      fmt(well_code),
                    "生产日期":      fmt(rpt.report_date),
                    "注水方式":   fmt(rpt.injection_mode),
                    "生产时间": fmt(rpt.prod_hours),
                    "干线压力（泵压）": fmt(rpt.trunk_pressure),
                    "油压":  fmt(rpt.oil_pressure),
                    "套压":  fmt(rpt.casing_pressure),
                    "井口油压": fmt(rpt.wellhead_pressure),
                    "日配注入量": fmt(rpt.plan_inject),
                    "日注水量": fmt(rpt.actual_inject),
                    "备注":       fmt(rpt.remark),
                    "一段水表数":   fmt(rpt.meter_stage1),
                    "二段水表数":   fmt(rpt.meter_stage2),
                    "三段水表数":   fmt(rpt.meter_stage3),
                    })

        if not rows:
            QMessageBox.warning(self, "无数据", f"{team_txt} 在 {rpt_date} 没有日报")
            return

        # 弹出文件保存对话框
        fname, _ = QFileDialog.getSaveFileName(
            self, "保存为 Excel", f"{team_txt}_{rpt_date}.xlsx", "Excel 文件 (*.xlsx)"
        )
        if not fname:
            return

        df = pd.DataFrame(rows)
        # 用 ExcelWriter 并指定 engine='xlsxwriter'
        with pd.ExcelWriter(fname, engine='xlsxwriter') as writer:
            # 1) 把 DataFrame 从第二行开始写入（保留第1行为标题）
            df.to_excel(writer,
                        sheet_name='Sheet1',
                        index=False,
                        startrow=1)

            # 2) 拿到 workbook / worksheet
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # 3) 定义标题单元格格式
            title_fmt = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'bold': True,
                'font_name': '宋体',
                'font_size': 22,
            })

            # 4) 计算要合并到第几列（0-based）
            last_col = len(df.columns) - 1

            # 5) 合并 A1 到 (row=0, col=last_col)，写入标题文本
            worksheet.merge_range(0, 0, 0, last_col,
                                  f"{team_txt}{rpt_date}", title_fmt)
            # —— ② 表头格式 ——
            header_fmt = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': '宋体',
                'font_size': 14,
                'border': 1,
            })
            # 第二行是表头：行号 1（0-based）
            worksheet.set_row(1, None, header_fmt)


            # —— ③ 数据单元格格式 ——
            data_fmt = workbook.add_format({
                'font_name': '宋体',   # 数据单元格字体
                'font_size': 14,
                'align':     'center',
                'valign':    'vcenter',
                'border':    1,           # 四周细实线边框
                'bold':      False,
            })
            first_data_row = 2
            last_data_row = 1 + len(df)
            worksheet.conditional_format(
                first_data_row, 0,
                last_data_row, last_col,
                {
                    'type': 'no_errors',  # 匹配所有非错误单元格 → 整块区域都会被格式化
                    'format': data_fmt
                }
            )

            worksheet.set_column(0, last_col, 19.63)

        QMessageBox.information(self, "导出成功", f"已保存到：\n{fname}")
        self.accept()


# -------- 日报输入对话框 --------
class DailyReportDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("日报填写／修改")
        form = QFormLayout(self)

        # 日期
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("日期", self.date_edit)

        # 注水方式
        self.mode_edit = QLineEdit()
        form.addRow("注水方式", self.mode_edit)

        # 生产时长
        self.prod_spin = QDoubleSpinBox()
        self.prod_spin.setRange(0, 1e4); self.prod_spin.setDecimals(2)
        form.addRow("生产时长(h)", self.prod_spin)

        # 各类压力
        self.trunk_spin = QDoubleSpinBox(); self.trunk_spin.setRange(0,1e4); self.trunk_spin.setDecimals(3)
        form.addRow("干线压(MPa)", self.trunk_spin)
        self.oil_spin = QDoubleSpinBox(); self.oil_spin.setRange(0,1e4); self.oil_spin.setDecimals(3)
        form.addRow("油压(MPa)", self.oil_spin)
        self.casing_spin = QDoubleSpinBox(); self.casing_spin.setRange(0,1e4); self.casing_spin.setDecimals(3)
        form.addRow("套压(MPa)", self.casing_spin)
        self.wellhead_spin = QDoubleSpinBox(); self.wellhead_spin.setRange(0,1e4); self.wellhead_spin.setDecimals(3)
        form.addRow("井口压(MPa)", self.wellhead_spin)

        # 注水量
        self.plan_spin = QDoubleSpinBox(); self.plan_spin.setRange(0,1e6); self.plan_spin.setDecimals(2)
        form.addRow("计划注水(m³)", self.plan_spin)
        self.actual_spin = QDoubleSpinBox(); self.actual_spin.setRange(0,1e6); self.actual_spin.setDecimals(2)
        form.addRow("实际注水(m³)", self.actual_spin)

        # 备注
        self.remark_edit = QTextEdit()
        form.addRow("备注", self.remark_edit)

        # 计量阶段
        self.m1 = QDoubleSpinBox(); self.m1.setRange(0,1e4); self.m1.setDecimals(2)
        form.addRow("计量阶段1", self.m1)
        self.m2 = QDoubleSpinBox(); self.m2.setRange(0,1e4); self.m2.setDecimals(2)
        form.addRow("计量阶段2", self.m2)
        self.m3 = QDoubleSpinBox(); self.m3.setRange(0,1e4); self.m3.setDecimals(2)
        form.addRow("计量阶段3", self.m3)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        # 如果有 data，则预填表单
        if data:
            # data: ORM DailyReport
            self.date_edit.setDate(QDate(data.report_date.year,
                                         data.report_date.month,
                                         data.report_date.day))
            self.mode_edit.setText(data.injection_mode or "")
            self.prod_spin.setValue(data.prod_hours or 0)
            self.trunk_spin.setValue(data.trunk_pressure or 0)
            self.oil_spin.setValue(data.oil_pressure or 0)
            self.casing_spin.setValue(data.casing_pressure or 0)
            self.wellhead_spin.setValue(data.wellhead_pressure or 0)
            self.plan_spin.setValue(data.plan_inject or 0)
            self.actual_spin.setValue(data.actual_inject or 0)
            self.remark_edit.setPlainText(data.remark or "")
            self.m1.setValue(data.meter_stage1 or 0)
            self.m2.setValue(data.meter_stage2 or 0)
            self.m3.setValue(data.meter_stage3 or 0)

    def get_data(self):
        return {
            "report_date": self.date_edit.date().toPyDate(),
            "injection_mode": self.mode_edit.text().strip(),
            "prod_hours": self.prod_spin.value(),
            "trunk_pressure": self.trunk_spin.value(),
            "oil_pressure": self.oil_spin.value(),
            "casing_pressure": self.casing_spin.value(),
            "wellhead_pressure": self.wellhead_spin.value(),
            "plan_inject": self.plan_spin.value(),
            "actual_inject": self.actual_spin.value(),
            "remark": self.remark_edit.toPlainText().strip(),
            "meter_stage1": self.m1.value(),
            "meter_stage2": self.m2.value(),
            "meter_stage3": self.m3.value(),
        }


# -------- 简易表格模型 --------
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




# -------- 主页面 --------
class AdminPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("注水井多级管理")
        self.resize(1000, 600)

        # 工具栏
        self.toolbar = QToolBar()
        self.act_delete = QAction("级联删除", self)
        self.toolbar.addAction(self.act_delete)
        self.act_delete.triggered.connect(self._delete_current)

        self.act_add = QAction("添加记录", self)
        self.toolbar.addAction(self.act_add)
        self.act_add.triggered.connect(self._add_current)

        # —— 新增导出按钮 ——
        self.act_export = QAction("导出水报", self)
        self.toolbar.addAction(self.act_export)
        self.act_export.triggered.connect(self._on_export_reports)

        # 左树 + 右表
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.clicked.connect(self._on_tree_clicked)
        self.table = QTableView()

        # 右键菜单
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.table)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(splitter)

        self._current_level = None
        self._current_id = None
        self._daily_reports = []

        self._build_tree()

    def _on_export_reports(self):
        dlg = ExportDialog(self)
        dlg.exec_()

    # ---- 构建树 ----
    def _build_tree(self):
        model = QStandardItemModel()
        root_item = model.invisibleRootItem()

        # —— 添加可见根节点标题 ——
        it_root = QStandardItem("报表管理")
        it_root.setEditable(False)         # 根节点通常不允许编辑
        it_root.setData((None,None), Qt.UserRole + 1)
        root_item.appendRow(it_root)

        # —— 原来的各级节点都挂到 it_root 下面 ——
        for area in list_root():
            it_area = QStandardItem(f"区 | {area.area_name}")
            it_area.setData(("area", area.area_id), Qt.UserRole + 1)
            it_root.appendRow(it_area)

            for team in list_children("area", area.area_id):
                it_team = QStandardItem(f"班 | {team.team_name}")
                it_team.setData(("team", team.team_id), Qt.UserRole + 1)
                it_area.appendRow(it_team)

                for room in list_children("team", team.team_id):
                    it_room = QStandardItem(f"间 | {room.room_no}")
                    it_room.setData(("room", room.room_id), Qt.UserRole + 1)
                    it_team.appendRow(it_room)

                    for well in list_children("room", room.room_id):
                        it_well = QStandardItem(f"井 | {well.well_code}")
                        it_well.setData(("well", well.well_id), Qt.UserRole + 1)
                        it_room.appendRow(it_well)

        self.tree.setModel(model)
        self.tree.expandAll()



    # ---- 树节点点击 ----
    def _on_tree_clicked(self, index):
        level, obj_id = index.data(Qt.UserRole + 1)
        self._current_level, self._current_id = level, obj_id

        rows, headers = [], []



        if level is None:
            return

        if level == "well":
            # 1) 取出该井所有日报
            reports = list_children("well", obj_id)
            self._daily_reports = reports  # 保存 ORM 对象

            # 2) 构建完整列头（根据 DailyReport ORM 的字段）
            headers = [
                "日期", "注水方式", "生产时长(h)",
                "干线压(MPa)", "油压(MPa)", "套压(MPa)", "井口压(MPa)",
                "计划注水(m³)", "实际注水(m³)", "备注",
                "计量阶段1", "计量阶段2", "计量阶段3"
            ]

            # 3) 把每条日报转成行数据
            rows = [
                (
                    fmt(r.report_date), fmt(r.injection_mode), fmt(r.prod_hours),
                    fmt(r.trunk_pressure), fmt(r.oil_pressure), fmt(r.casing_pressure),
                    fmt(r.wellhead_pressure), fmt(r.plan_inject), fmt(r.actual_inject),
                    fmt(r.remark),
                    fmt(r.meter_stage1), fmt(r.meter_stage2), fmt(r.meter_stage3)
                )
                for r in reports
            ]

        else:
            # 非井节点 → 显示下一层基本信息
            children = list_children(level, obj_id)
            map_func = {
                "area": lambda x: (x.team_id, x.team_name),
                "team": lambda x: (x.room_id, x.room_no),
                "room": lambda x: (x.well_id, x.well_code),
            }
            headers = ["ID", "名称/编号"]
            rows = [map_func[level](c) for c in children]

        self.table.setModel(SimpleTableModel(headers, rows))

    # ---- 删除当前节点 ----
    def _delete_current(self):
        if not self._current_level:
            return
        if QMessageBox.question(
            self, "确认", "级联删除当前节点及其所有下级？",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.No:
            return
        delete_entity(self._current_level, self._current_id)
        QMessageBox.information(self, "完成", "已删除")
        self._build_tree()
        self.table.setModel(SimpleTableModel([], []))

    def _add_current(self):
        # if not self._current_level:
        #     QMessageBox.warning(self, "错误", "请先选择一个节点")
        #     return


        if self._current_level == "area":
            text, ok = QInputDialog.getText(self, "新建班组", "请输入班组名称:")
            if ok and text:
                team_name = text.strip()
                team_no, ok2 = QInputDialog.getInt(self, "编号", "请输入班组编号:")
                if ok2:
                    from dataBase.water_report_dao import upsert_prod_team
                    upsert_prod_team(self._current_id, team_no=team_no, team_name=team_name)

        elif self._current_level == "team":
            text, ok = QInputDialog.getText(self, "新建计量间", "请输入计量间号:")
            if ok and text:
                room_no = text.strip()
                from dataBase.water_report_dao import upsert_meter_room
                upsert_meter_room(self._current_id, room_no=room_no)

        elif self._current_level == "room":
            text, ok = QInputDialog.getText(self, "新建井", "请输入井编号:")
            if ok and text:
                well_code = text.strip()
                from dataBase.water_report_dao import upsert_well
                upsert_well(self._current_id, well_code=well_code)


        elif self._current_level == "well":

            dlg = DailyReportDialog(self)

            if dlg.exec_() == QDialog.Accepted:
                rpt = dlg.get_data()
                upsert_daily_report(self._current_id, rpt)

        elif self._current_level is None:
            text, ok = QInputDialog.getText(self, "新建作业区", "请输入作业区名称:")
            if ok and text:
                area_name = text.strip()
                from dataBase.water_report_dao import upsert_work_area
                upsert_work_area(area_name)


        # 刷新树和表格
        self._build_tree()
        self.table.setModel(SimpleTableModel([], []))



    def _on_table_context_menu(self, pos):
        if self._current_level != "well":
            return
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self.table)
        edit_act = menu.addAction("修改报表")
        delete_act = menu.addAction("删除报表")
        act = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if act == edit_act:
            row = idx.row()
            rpt_obj = self._daily_reports[row]
            dlg = DailyReportDialog(self, data=rpt_obj)
            if dlg.exec_() == QDialog.Accepted:
                new_data = dlg.get_data()
                # 使用相同接口更新
                upsert_daily_report(self._current_id, new_data)
                # 重新加载视图
                self._on_tree_clicked(self.tree.currentIndex())
        elif act==delete_act:
            row = idx.row()
            rpt_obj = self._daily_reports[row]
            delete_entity("report", rpt_obj.report_id)
            QMessageBox.information(self, "完成", "已删除")
            self._on_tree_clicked(self.tree.currentIndex())


class AdvancedPage(QWidget):
    def __init__(self):
        super().__init__()
        self.permission_list=[]
        self.setWindowTitle("注水井多级管理")
        self.resize(1000, 600)

        # 工具栏
        self.toolbar = QToolBar()
        self.act_delete = QAction("级联删除", self)
        self.toolbar.addAction(self.act_delete)
        self.act_delete.triggered.connect(self._delete_current)

        self.act_add = QAction("添加记录", self)
        self.toolbar.addAction(self.act_add)
        self.act_add.triggered.connect(self._add_current)

        # 左树 + 右表
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.clicked.connect(self._on_tree_clicked)
        self.table = QTableView()

        # 右键菜单
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.table)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(splitter)

        self._current_level = None
        self._current_id = None
        self._daily_reports = []


    def put_account_info(self,permission_list):
        self.permission_list=permission_list

    # ---- 构建树 ----
    def build_tree(self):
        model = QStandardItemModel()
        root_item = model.invisibleRootItem()

        # —— 添加可见根节点标题 ——
        it_root = QStandardItem("报表管理")
        it_root.setEditable(False)         # 根节点通常不允许编辑
        it_root.setData((None,None), Qt.UserRole + 1)
        root_item.appendRow(it_root)

        it_team = QStandardItem()

        for area in list_root():
            if area.area_name==self.permission_list[1]:
                self.area_id=area.area_id
                for team in list_children("area", self.area_id):
                    if team.team_name == self.permission_list[2]:
                        self.team_id = team.team_id
                        text = f"班 | {team.team_name}"
                        it_team.setText(text)
                        it_team.setData(("team", team.team_id), Qt.UserRole + 1)

        it_root.appendRow(it_team)

        for room in list_children("team", self.team_id):
            it_room = QStandardItem(f"间 | {room.room_no}")
            it_room.setData(("room", room.room_id), Qt.UserRole + 1)
            it_team.appendRow(it_room)

            for well in list_children("room", room.room_id):
                it_well = QStandardItem(f"井 | {well.well_code}")
                it_well.setData(("well", well.well_id), Qt.UserRole + 1)
                it_room.appendRow(it_well)

        self.tree.setModel(model)
        self.tree.expandAll()



    # ---- 树节点点击 ----
    def _on_tree_clicked(self, index):
        level, obj_id = index.data(Qt.UserRole + 1)
        self._current_level, self._current_id = level, obj_id

        rows, headers = [], []

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

        if level is None:
            return

        if level == "well":
            # 1) 取出该井所有日报
            reports = list_children("well", obj_id)
            self._daily_reports = reports  # 保存 ORM 对象

            # 2) 构建完整列头（根据 DailyReport ORM 的字段）
            headers = [
                "日期", "注水方式", "生产时长(h)",
                "干线压(MPa)", "油压(MPa)", "套压(MPa)", "井口压(MPa)",
                "计划注水(m³)", "实际注水(m³)", "备注",
                "计量阶段1", "计量阶段2", "计量阶段3"
            ]

            # 3) 把每条日报转成行数据
            rows = [
                (
                    _fmt(r.report_date), _fmt(r.injection_mode), _fmt(r.prod_hours),
                    _fmt(r.trunk_pressure), _fmt(r.oil_pressure), _fmt(r.casing_pressure),
                    _fmt(r.wellhead_pressure), _fmt(r.plan_inject), _fmt(r.actual_inject),
                    _fmt(r.remark),
                    _fmt(r.meter_stage1), _fmt(r.meter_stage2), _fmt(r.meter_stage3)
                )
                for r in reports
            ]

        else:
            # 非井节点 → 显示下一层基本信息
            children = list_children(level, obj_id)
            map_func = {
                "area": lambda x: (x.team_id, x.team_name),
                "team": lambda x: (x.room_id, x.room_no),
                "room": lambda x: (x.well_id, x.well_code),
            }
            headers = ["ID", "名称/编号"]
            rows = [map_func[level](c) for c in children]

        self.table.setModel(SimpleTableModel(headers, rows))

    # ---- 删除当前节点 ----
    def _delete_current(self):
        if not self._current_level:
            return
        if QMessageBox.question(
            self, "确认", "级联删除当前节点及其所有下级？",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.No:
            return
        delete_entity(self._current_level, self._current_id)
        QMessageBox.information(self, "完成", "已删除")
        self._build_tree()
        self.table.setModel(SimpleTableModel([], []))

    def _add_current(self):
        # if not self._current_level:
        #     QMessageBox.warning(self, "错误", "请先选择一个节点")
        #     return


        if self._current_level == "area":
            text, ok = QInputDialog.getText(self, "新建班组", "请输入班组名称:")
            if ok and text:
                team_name = text.strip()
                team_no, ok2 = QInputDialog.getInt(self, "编号", "请输入班组编号:")
                if ok2:
                    from dataBase.water_report_dao import upsert_prod_team
                    upsert_prod_team(self._current_id, team_no=team_no, team_name=team_name)

        elif self._current_level == "team":
            text, ok = QInputDialog.getText(self, "新建计量间", "请输入计量间号:")
            if ok and text:
                room_no = text.strip()
                from dataBase.water_report_dao import upsert_meter_room
                upsert_meter_room(self._current_id, room_no=room_no)

        elif self._current_level == "room":
            text, ok = QInputDialog.getText(self, "新建井", "请输入井编号:")
            if ok and text:
                well_code = text.strip()
                from dataBase.water_report_dao import upsert_well
                upsert_well(self._current_id, well_code=well_code)


        elif self._current_level == "well":

            dlg = DailyReportDialog(self)

            if dlg.exec_() == QDialog.Accepted:
                rpt = dlg.get_data()
                upsert_daily_report(self._current_id, rpt)

        elif self._current_level is None:
            return


        # 刷新树和表格
        self._build_tree()
        self.table.setModel(SimpleTableModel([], []))



    def _on_table_context_menu(self, pos):
        if self._current_level != "well":
            return
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self.table)
        edit_act = menu.addAction("修改报表")
        delete_act = menu.addAction("删除报表")
        act = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if act == edit_act:
            row = idx.row()
            rpt_obj = self._daily_reports[row]
            dlg = DailyReportDialog(self, data=rpt_obj)
            if dlg.exec_() == QDialog.Accepted:
                new_data = dlg.get_data()
                # 使用相同接口更新
                upsert_daily_report(self._current_id, new_data)
                # 重新加载视图
                self._on_tree_clicked(self.tree.currentIndex())
        elif act==delete_act:
            row = idx.row()
            rpt_obj = self._daily_reports[row]
            delete_entity("report", rpt_obj.report_id)
            QMessageBox.information(self, "完成", "已删除")
            self._on_tree_clicked(self.tree.currentIndex())


# ---- 运行 ----
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AdminPage()

    win.show()

    sys.exit(app.exec_())
