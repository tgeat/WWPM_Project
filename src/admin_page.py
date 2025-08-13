import sys, warnings, pathlib,traceback

from decimal import Decimal
from datetime import date, datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QTreeView, QTableView, QSplitter, QTreeWidget,
    QVBoxLayout, QToolBar, QAction, QMessageBox, QInputDialog,
    QDialog, QFormLayout, QLineEdit, QDateEdit, QSpinBox,
    QDoubleSpinBox, QTextEdit, QDialogButtonBox, QMenu, QComboBox,QListWidgetItem,
    QTreeWidgetItem, QFileDialog, QHBoxLayout,QLabel, QListWidget, QPushButton
)

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate, QMimeData
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QDrag
from src.formula import FormulaImportDialog
# 屏蔽 sip 警告
warnings.filterwarnings("ignore", category=DeprecationWarning)
# 保证 src/ 在导入路径
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from database.water_report_dao import (
    list_root, list_children, delete_entity, upsert_daily_report, DBSession,Bao
)
from database.db_schema import DailyReport, SessionLocal, OilWellDatas, Well, Bao, Platformer
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

#导出拖拽
class DraggableTreeWidget(QTreeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
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
        if len(sel) != 1 or target is None:
            event.ignore()
            return

        dragged = sel[0]
        origP = dragged.parent()
        pos = self.dropIndicatorPosition()
        newP = target.parent() if pos != QTreeWidget.OnItem else target

        dragged_data = dragged.data(0, Qt.UserRole)
        target_data = target.data(0, Qt.UserRole)
        dragged_type = dragged_data[0] if dragged_data else None
        target_type = target_data[0] if target_data else None

        # 基础保护
        if not dragged_type or not target_type:
            event.ignore()
            return

        if pos == QTreeWidget.OnItem:
            # —— 规则 1：井 → 水报
            if dragged_type == "well" and target_type == "bao":
                if "水报" in target.text(0):
                    super().dropEvent(event)
                    return

            # —— 规则 2：井 → 平台（油报）
            if dragged_type == "well" and target_type == "platformer":
                parent_bao = target.parent()
                if parent_bao and parent_bao.data(0, Qt.UserRole):
                    parent_type, _ = parent_bao.data(0, Qt.UserRole)
                    if parent_type == "bao" and "油报" in parent_bao.text(0):
                        super().dropEvent(event)
                        return

            # —— 规则 3：平台 → 油报
            if dragged_type == "platformer" and target_type == "bao":
                if "油报" in target.text(0):
                    super().dropEvent(event)
                    return

        elif pos in (QTreeWidget.BelowItem, QTreeWidget.AboveItem):
            # 规则 4：同层级节点间允许排序
            if origP and newP and origP == newP:
                super().dropEvent(event)
                return

        # 默认禁止其他拖拽
        event.ignore()

#导出对话框
class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出报表")  # 改为通用标题
        self.resize(600, 800)
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

        # # —— 报类型选择
        # self.report_type_combo = QComboBox()
        # self.report_type_combo.addItems(["水报", "油报"])
        # form.addRow("选择报类型：", self.report_type_combo)

        # 新增两个按钮
        btn_layout = QHBoxLayout()
        self.btn_all_water = QPushButton("全部水报")
        self.btn_all_oil = QPushButton("全部油报")
        btn_layout.addWidget(self.btn_all_water)
        btn_layout.addWidget(self.btn_all_oil)

        # —— 拖拽树
        self.tree = DraggableTreeWidget()
        self.tree.setHeaderLabel("计量间 → 报 → 井/平台（拖拽调整顺序）")

        # 连接勾选变化信号
        self.tree.itemChanged.connect(self._on_tree_item_changed)

        # —— 确认/取消
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_export)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addLayout(btn_layout)  # 添加按钮行
        lay.addWidget(self.tree, 1)
        lay.addWidget(buttons)

        # 信号关联
        self.area_combo.currentIndexChanged.connect(self._reload_teams)
        self.team_combo.currentIndexChanged.connect(self._reload_tree)
        # self.report_type_combo.currentIndexChanged.connect(self._reload_tree)
        self.btn_all_water.clicked.connect(self._check_all_water)
        self.btn_all_oil.clicked.connect(self._check_all_oil)
        # 初始化
        self._reload_teams()

    def _reload_teams(self):
        """根据 area_combo 更新 team_combo"""
        try:
            self.team_combo.clear()
            area_id = self.area_combo.currentData()  # 获取选中的作业区 ID

            # 获取该作业区下的所有班组
            teams = list_children("area", area_id)

            for team in teams:
                self.team_combo.addItem(team.team_name, team.team_id)  # 添加班组到下拉框

            # 更新完班组后，刷新树
            self._reload_tree()

        except Exception as e:
            print(f"Error during team reload: {e}")  # 捕获异常并打印错误信息

    def _reload_tree(self):
        """根据 team_combo 填充左侧的可拖拽树"""
        self.tree.clear()

        team_id = self.team_combo.currentData()

        try:
            with DBSession() as db:  # 保持会话打开直到所有数据处理完成
                # 加载房间
                rooms = list_children("team", team_id)

                for room in rooms:
                    room_item = QTreeWidgetItem([room.room_no])
                    room_item.setFlags(room_item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
                    room_item.setData(0, Qt.UserRole, ("room", room.id))
                    self.tree.addTopLevelItem(room_item)

                    # 加载报
                    baos = list_children("room", room.id)

                    for bao in baos:
                        # 强制加载类型字段，防止懒加载异常
                        bao_typeid = bao.bao_typeid

                        bao_item = QTreeWidgetItem([bao_typeid])
                        bao_item.setFlags(bao_item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
                        bao_item.setData(0, Qt.UserRole, ("bao", bao.id))
                        bao_item.setCheckState(0, Qt.Unchecked)
                        room_item.addChild(bao_item)

                        # 获取包下的子节点（井或平台）
                        children = list_children("bao", bao.id)

                        if "水报" in bao_typeid:
                            for well in children:
                                # debug 打印
                                well_item = QTreeWidgetItem([well.well_code])
                                well_item.setFlags(well_item.flags() | Qt.ItemIsDragEnabled)
                                well_item.setData(0, Qt.UserRole, ("well", well.id))
                                bao_item.addChild(well_item)

                        elif "油报" in bao_typeid:
                            for platform in children:

                                platform_item = QTreeWidgetItem([platform.platformer_id])
                                platform_item.setFlags(
                                    platform_item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
                                platform_item.setData(0, Qt.UserRole, ("platformer", platform.id))
                                bao_item.addChild(platform_item)

                                # 这里尝试获取平台下的井
                                platform_wells = list_children("platform", platform.id)

                                for well in platform_wells:
                                    well_item = QTreeWidgetItem([well.well_code])
                                    well_item.setFlags(well_item.flags() | Qt.ItemIsDragEnabled)
                                    well_item.setData(0, Qt.UserRole, ("well", well.id))
                                    platform_item.addChild(well_item)

            self.tree.expandAll()

        except Exception as e:
            print(f"Error during tree reload: {e}")

    def _check_all_water(self):
        """勾选全部水报，取消全部油报"""
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            room_item = self.tree.topLevelItem(i)
            for j in range(room_item.childCount()):
                bao_item = room_item.child(j)
                bao_type = bao_item.text(0)
                if "水报" in bao_type:
                    bao_item.setCheckState(0, Qt.Checked)
                elif "油报" in bao_type:
                    bao_item.setCheckState(0, Qt.Unchecked)
        self.tree.blockSignals(False)

    def _check_all_oil(self):
        """勾选全部油报，取消全部水报"""
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            room_item = self.tree.topLevelItem(i)
            for j in range(room_item.childCount()):
                bao_item = room_item.child(j)
                bao_type = bao_item.text(0)
                if "油报" in bao_type:
                    bao_item.setCheckState(0, Qt.Checked)
                elif "水报" in bao_type:
                    bao_item.setCheckState(0, Qt.Unchecked)
        self.tree.blockSignals(False)

    def _on_tree_item_changed(self, item, column):
        if column != 0:
            return

        self.tree.blockSignals(True)

        has_water = False
        has_oil = False
        for i in range(self.tree.topLevelItemCount()):
            room_item = self.tree.topLevelItem(i)
            for j in range(room_item.childCount()):
                bao_item = room_item.child(j)
                if bao_item.checkState(0) == Qt.Checked:
                    bao_type = bao_item.text(0)
                    if "水报" in bao_type:
                        has_water = True
                    elif "油报" in bao_type:
                        has_oil = True

        if has_water and has_oil:
            QMessageBox.warning(self, "选择错误", "请勿同时勾选水报和油报，请先取消其中一种的勾选。")
            # 撤销当前勾选操作
            if item.checkState(0) == Qt.Checked:
                item.setCheckState(0, Qt.Unchecked)
            else:
                item.setCheckState(0, Qt.Checked)

        self.tree.blockSignals(False)

    def _gather_order(self):
        """读取当前树内用户排序，且只收集用户勾选的报节点"""
        order = []
        for i in range(self.tree.topLevelItemCount()):
            room_item = self.tree.topLevelItem(i)
            room_no = room_item.text(0)
            room_id = room_item.data(0, Qt.UserRole)[1]

            baos = []
            for j in range(room_item.childCount()):
                bao_item = room_item.child(j)
                bao_type = bao_item.text(0)
                bao_id = bao_item.data(0, Qt.UserRole)[1]

                # ✅ 如果没有勾选此报节点，则跳过
                if bao_item.checkState(0) != Qt.Checked:
                    continue

                wells = []
                if "水报" in bao_type:
                    for k in range(bao_item.childCount()):
                        well_item = bao_item.child(k)
                        well_code = well_item.text(0)
                        well_id = well_item.data(0, Qt.UserRole)[1]
                        wells.append((well_code, well_id))

                elif "油报" in bao_type:
                    platforms = []
                    for k in range(bao_item.childCount()):
                        platform_item = bao_item.child(k)
                        platform_id = platform_item.data(0, Qt.UserRole)[1]

                        platform_wells = []
                        for l in range(platform_item.childCount()):
                            well_item = platform_item.child(l)
                            well_code = well_item.text(0)
                            well_id = well_item.data(0, Qt.UserRole)[1]
                            platform_wells.append((well_code, well_id))

                        platforms.append((platform_item.text(0), platform_id, platform_wells))

                    for _, _, platform_wells in platforms:
                        wells.extend(platform_wells)

                baos.append((bao_type, bao_id, wells))

            order.append((room_no, room_id, baos))

        return order

    def _check_mixed_report_selection(self):
        """检测当前树中是否同时勾选了水报和油报"""
        has_water = False
        has_oil = False
        for i in range(self.tree.topLevelItemCount()):
            room_item = self.tree.topLevelItem(i)
            for j in range(room_item.childCount()):
                bao_item = room_item.child(j)
                if bao_item.checkState(0) == Qt.Checked:
                    bao_type = bao_item.text(0)
                    if "水报" in bao_type:
                        has_water = True
                    elif "油报" in bao_type:
                        has_oil = True
                    # 早退出优化
                    if has_water and has_oil:
                        return True
        return False

    def _on_export(self):
        import traceback
        try:
            team_id = self.team_combo.currentData()
            team_txt = self.team_combo.currentText()
            rpt_date = self.date_edit.date().toPyDate()

            rows = []

            order = self._gather_order()
            has_water = False
            has_oil = False
            for _, _, baos in order:
                for bao_type, _, _ in baos:
                    if "水报" in bao_type:
                        has_water = True
                    elif "油报" in bao_type:
                        has_oil = True
            if has_water and has_oil:
                QMessageBox.warning(self, "选择错误", "请勿同时勾选水报和油报，请先取消其中一种的勾选。")
                return

            with SessionLocal() as db:
                rooms = list_children("team", team_id)

                for room_no, room_id, baos in self._gather_order():
                    room_obj = next((r for r in rooms if r.id == room_id), None)
                    if room_obj is None:
                        print(f"[WARN] 找不到房间对象，room_id={room_id}")
                        continue

                    baos_in_db = db.query(Bao).filter_by(room_id=room_id).all()

                    for bao_type, bao_id, wells in baos:
                        bao_obj = next((b for b in baos_in_db if b.id == bao_id), None)
                        if bao_obj is None:
                            print(f"[WARN] 找不到包对象，bao_id={bao_id}")
                            continue

                        for well_code, well_id in wells:
                            well_obj = None
                            if "水报" in bao_type:
                                well_obj = next((w for w in bao_obj.wells if w.id == well_id), None)
                            elif "油报" in bao_type:
                                platforms = list(bao_obj.platforms)
                                for platform in platforms:
                                    well_obj = next((w for w in platform.wells if w.id == well_id), None)
                                    if well_obj:
                                        break

                            if not well_obj:
                                print(f"[WARN] 找不到井对象，well_id={well_id}")
                                continue

                            rpt = None
                            if "油报" in bao_type:
                                rpt = db.query(OilWellDatas).filter_by(
                                    well_id=well_obj.id,
                                    create_time=rpt_date
                                ).first()
                            else:
                                rpt = db.query(DailyReport).filter_by(
                                    well_id=well_obj.id,
                                    report_date=rpt_date
                                ).first()

                            if not rpt:
                                print(f"[INFO] 无日报数据：井id={well_obj.id}, 日期={rpt_date}, 类型={bao_type}")
                                continue

                            if "油报" in bao_type:
                                row = {
                                    "间": fmt(room_obj.room_no),

                                    "平台": fmt(rpt.platform),
                                    "日期": fmt(rpt.create_time),
                                    "井号": fmt(well_code),
                                    "生产时间": fmt(rpt.prod_hours),
                                    "A2冲程 （公式）": fmt(rpt.a2_stroke),
                                    "A2冲次 （公式）": fmt(rpt.a2_frequency),
                                    "功图冲次": fmt(rpt.work_stroke),
                                    "有效排液冲程": fmt(rpt.effective_stroke),
                                    "套压": fmt(rpt.casing_pressure),
                                    "油压": fmt(rpt.oil_pressure),
                                    "回压": fmt(rpt.back_pressure),
                                    "A2(24h)液量": fmt(rpt.a2_24h_liquid),
                                    "液量": fmt(rpt.liquid1),
                                    "油量": fmt(rpt.oil_volume),
                                    "化验含水": fmt(rpt.lab_water_cut),
                                    "上报含水": fmt(rpt.reported_water),
                                    "波动范围": fmt(rpt.fluctuation_range),
                                    "时间标记": fmt(rpt.time_sign),
                                    "液量/斗数": fmt(rpt.liquid_per_bucket),
                                    "是否合量斗数":fmt(rpt.total_bucket_sign),
                                    "合量斗数": fmt(rpt.total_bucket),
                                    "充满系数液量": fmt(rpt.fill_coeff_liquid),
                                    "和": fmt(rpt.sum_value),
                                    "液量": fmt(rpt.liquid2),
                                    "分产系数": fmt(rpt.production_coeff),
                                    "停产时间": fmt(rpt.shutdown_time),
                                    "备注": fmt(rpt.remark),
                                    "理论排量-液量差值": fmt(rpt.theory_diff),
                                    "理论排量": fmt(rpt.theory_displacement),
                                    "k值": fmt(rpt.k_value),
                                    "充满系数": fmt(rpt.fill_coeff_test),
                                    "上次动管柱时间": fmt(rpt.last_tubing_time),
                                    "泵径": fmt(rpt.pump_diameter),
                                    "区块": fmt(rpt.block),
                                    "变压器": fmt(rpt.transformer),
                                    "日产液": fmt(rpt.daily_liquid),
                                    "日产油": fmt(rpt.daily_oil),
                                    "井次": fmt(rpt.well_times),
                                    "时间": fmt(rpt.production_time),
                                    "产油": fmt(rpt.total_oil),
                                    "时间": fmt(rpt.production_time),
                                    "产油": fmt(rpt.total_oil),
                                    "憋压数据": fmt(rpt.press_data),
                                }
                                rows.append(row)
                            else:
                                rows.append({
                                    "日期": fmt(rpt.report_date),
                                    "井号": fmt(well_code),
                                    "注水方式": fmt(rpt.injection_mode),
                                    "生产时长(h)": fmt(rpt.prod_hours),
                                    "干线压(MPa)": fmt(rpt.trunk_pressure),
                                    "油压(MPa)": fmt(rpt.oil_pressure),
                                    "套压(MPa)": fmt(rpt.casing_pressure),
                                    "井口压(MPa)": fmt(rpt.wellhead_pressure),
                                    "计划注水(m³)": fmt(rpt.plan_inject),
                                    "实际注水(m³)": fmt(rpt.actual_inject),
                                    "备注": fmt(rpt.remark),
                                    "计量阶段1": fmt(rpt.meter_stage1),
                                    "计量阶段2": fmt(rpt.meter_stage2),
                                    "计量阶段3": fmt(rpt.meter_stage3),
                                })
            if not rows:
                QMessageBox.warning(self, "无数据", f"{team_txt} 在 {rpt_date} 没有日报")
                return

            # 决定列顺序
            if has_oil:
                EXPORT_COLUMNS = [
                    "间", "平台", "日期", "井号", "生产时间", "A2冲程 （公式）", "A2冲次 （公式）", "功图冲次",
                    "有效排液冲程", "套压", "油压", "回压", "A2(24h)液量", "液量", "油量", "化验含水", "上报含水",
                    "波动范围", "时间标记", "液量/斗数", "合量斗数", "充满系数液量", "和", "液量", "分产系数",
                    "停产时间", "备注", "理论排量-液量差值", "理论排量", "k值", "充满系数", "上次动管柱时间",
                    "泵径", "区块", "变压器", "日产液", "日产油", "井次", "产油时间1", "产油量1", "产油时间2",
                    "产油量2", "憋压数据"
                ]
            else:
                EXPORT_COLUMNS = [
                    "日期", "井号", "注水方式", "生产时长(h)", "干线压(MPa)", "油压(MPa)", "套压(MPa)",
                    "井口压(MPa)", "计划注水(m³)", "实际注水(m³)", "备注", "计量阶段1", "计量阶段2", "计量阶段3"
                ]

            default_filename = f"{team_txt}_{rpt_date}_{'油报' if has_oil else '水报'}.xlsx"
            fname, _ = QFileDialog.getSaveFileName(
                self, "保存为 Excel", default_filename, "Excel 文件 (*.xlsx)"
            )
            if not fname:
                return

            df = pd.DataFrame(rows)

            # 确保字段顺序 + 保留重复列名（通过 DataFrame 的 columns 参数）
            for col in EXPORT_COLUMNS:
                if col not in df.columns:
                    df[col] = ""  # 添加缺失字段

            df = df[EXPORT_COLUMNS]  # 重排序

            with pd.ExcelWriter(fname, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Sheet1', index=False, startrow=1)
                workbook = writer.book
                worksheet = writer.sheets['Sheet1']

                title_fmt = workbook.add_format({
                    'align': 'center', 'valign': 'vcenter', 'bold': True,
                    'font_name': '宋体', 'font_size': 22,
                })
                worksheet.merge_range(0, 0, 0, len(EXPORT_COLUMNS) - 1,
                                      f"{team_txt}{rpt_date}", title_fmt)

                header_fmt = workbook.add_format({
                    'bold': True, 'align': 'center', 'valign': 'vcenter',
                    'font_name': '宋体', 'font_size': 14, 'border': 1,
                })
                worksheet.set_row(1, None, header_fmt)

                data_fmt = workbook.add_format({
                    'font_name': '宋体', 'font_size': 14,
                    'align': 'center', 'valign': 'vcenter',
                    'border': 1, 'bold': False,
                })

                worksheet.conditional_format(
                    2, 0, 1 + len(df), len(EXPORT_COLUMNS) - 1,
                    {'type': 'no_errors', 'format': data_fmt}
                )

                worksheet.set_column(0, len(EXPORT_COLUMNS) - 1, 19.63)

            QMessageBox.information(self, "导出成功", f"已保存到：\n{fname}")
            self.accept()

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "导出失败", f"导出时发生异常:\n{e}")


# -------- 日报输入对话框 --------
# -------- 水报 --------
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

# -------- 油报 --------
class OilReportDialog(QDialog):
    def __init__(self, parent=None, platform=None, well_code=None,data=None):
        super().__init__(parent)
        self.platform = platform
        self.well_code = well_code
        self.setWindowTitle("日报填写／修改")
        self.resize(600, 600)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("日期", self.date_edit)

        self.prod_hours_spin = QDoubleSpinBox()
        self.prod_hours_spin.setRange(0, 1e4)
        self.prod_hours_spin.setDecimals(2)
        form_layout.addRow("生产时间", self.prod_hours_spin)

        # 新增字段：A2冲程
        self.a2_stroke_spin = QDoubleSpinBox()
        self.a2_stroke_spin.setRange(0, 1e4)
        self.a2_stroke_spin.setDecimals(2)
        form_layout.addRow("A2冲程", self.a2_stroke_spin)

        # 新增字段：A2冲次
        self.a2_frequency_spin = QDoubleSpinBox()
        self.a2_frequency_spin.setRange(0, 1e4)
        self.a2_frequency_spin.setDecimals(2)
        form_layout.addRow("A2冲次", self.a2_frequency_spin)

        self.casing_pressure_spin = QDoubleSpinBox()
        self.casing_pressure_spin.setRange(0, 1e4)
        self.casing_pressure_spin.setDecimals(3)
        form_layout.addRow("套压", self.casing_pressure_spin)

        self.oil_pressure_spin = QDoubleSpinBox()
        self.oil_pressure_spin.setRange(0, 1e4)
        self.oil_pressure_spin.setDecimals(3)
        form_layout.addRow("油压", self.oil_pressure_spin)

        self.back_pressure_spin = QDoubleSpinBox()
        self.back_pressure_spin.setRange(0, 1e4)
        self.back_pressure_spin.setDecimals(3)
        form_layout.addRow("回压", self.back_pressure_spin)

        self.time_sign_edit = QLineEdit()
        form_layout.addRow("时间标记", self.time_sign_edit)

        self.total_bucket_spin = QDoubleSpinBox()
        self.total_bucket_spin.setRange(0, 1e6)
        self.total_bucket_spin.setDecimals(2)
        form_layout.addRow("合量斗数", self.total_bucket_spin)

        self.press_data_edit = QLineEdit()
        form_layout.addRow("憋压数据", self.press_data_edit)

        self.remark_edit = QTextEdit()
        form_layout.addRow("备注", self.remark_edit)

        self.work_stroke_spin = QDoubleSpinBox()
        self.work_stroke_spin.setRange(0, 1e4)
        self.work_stroke_spin.setDecimals(2)
        form_layout.addRow("功图冲次", self.work_stroke_spin)

        self.effective_stroke_spin = QDoubleSpinBox()
        self.effective_stroke_spin.setRange(0, 1e4)
        self.effective_stroke_spin.setDecimals(2)
        form_layout.addRow("有效排液冲程", self.effective_stroke_spin)

        self.fill_coeff_test_spin = QDoubleSpinBox()
        self.fill_coeff_test_spin.setRange(0, 1)
        self.fill_coeff_test_spin.setDecimals(3)
        form_layout.addRow("充满系数", self.fill_coeff_test_spin)

        self.lab_water_cut_edit = QLineEdit()
        form_layout.addRow("化验含水", self.lab_water_cut_edit)

        self.reported_water_edit = QLineEdit()
        form_layout.addRow("上报含水", self.reported_water_edit)

        self.fill_coeff_liquid_spin = QDoubleSpinBox()
        self.fill_coeff_liquid_spin.setRange(0, 1e6)
        self.fill_coeff_liquid_spin.setDecimals(2)
        form_layout.addRow("充满系数液量", self.fill_coeff_liquid_spin)

        self.last_tubing_time_edit = QLineEdit()
        form_layout.addRow("上次动管柱时间", self.last_tubing_time_edit)

        self.pump_diameter_edit = QLineEdit()
        form_layout.addRow("泵径", self.pump_diameter_edit)

        self.block_edit = QLineEdit()
        form_layout.addRow("区块", self.block_edit)

        self.transformer_edit = QLineEdit()
        form_layout.addRow("变压器", self.transformer_edit)

        self.well_times_spin = QSpinBox()
        self.well_times_spin.setRange(0, 10000)
        form_layout.addRow("井次数", self.well_times_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        # 新增：如果传入已有数据，调用加载函数填充表单
        if data:
            self.load_data(data)

    def load_data(self, data):
        """把已有OilWellDatas数据填充到表单"""
        self.date_edit.setDate(QDate(data.create_time.year, data.create_time.month,
                                     data.create_time.day) if data.create_time else QDate.currentDate())
        self.prod_hours_spin.setValue(float(data.prod_hours) if data.prod_hours else 0)
        self.a2_stroke_spin.setValue(float(data.a2_stroke) if data.a2_stroke else 0)
        self.a2_frequency_spin.setValue(float(data.a2_frequency) if data.a2_frequency else 0)
        self.casing_pressure_spin.setValue(float(data.casing_pressure) if data.casing_pressure else 0)
        self.oil_pressure_spin.setValue(float(data.oil_pressure) if data.oil_pressure else 0)
        self.back_pressure_spin.setValue(float(data.back_pressure) if data.back_pressure else 0)
        self.time_sign_edit.setText(data.time_sign or "")
        self.total_bucket_spin.setValue(float(data.total_bucket) if data.total_bucket else 0)
        self.press_data_edit.setText(data.press_data or "")
        self.remark_edit.setPlainText(data.remark or "")
        self.work_stroke_spin.setValue(float(data.work_stroke) if data.work_stroke else 0)
        self.effective_stroke_spin.setValue(float(data.effective_stroke) if data.effective_stroke else 0)
        self.fill_coeff_test_spin.setValue(float(data.fill_coeff_test) if data.fill_coeff_test else 0)
        self.lab_water_cut_edit.setText(data.lab_water_cut or "")
        self.reported_water_edit.setText(data.reported_water or "")
        self.fill_coeff_liquid_spin.setValue(float(data.fill_coeff_liquid) if data.fill_coeff_liquid else 0)
        self.last_tubing_time_edit.setText(data.last_tubing_time or "")
        self.pump_diameter_edit.setText(data.pump_diameter or "")
        self.block_edit.setText(data.block or "")
        self.transformer_edit.setText(data.transformer or "")
        self.well_times_spin.setValue(int(data.well_times) if data.well_times else 0)

    def get_data(self):
        return {
            "platform": self.platform,
            "well_code": self.well_code,
            "create_time": self.date_edit.date().toPyDate(),
            "prod_hours": self.prod_hours_spin.value(),
            "a2_stroke": self.a2_stroke_spin.value(),
            "a2_frequency": self.a2_frequency_spin.value(),
            "casing_pressure": self.casing_pressure_spin.value(),
            "oil_pressure": self.oil_pressure_spin.value(),
            "back_pressure": self.back_pressure_spin.value(),
            "time_sign": self.time_sign_edit.text().strip(),
            # "total_bucket_sign": self.total_bucket_sign.text().strip(),
            "total_bucket": self.total_bucket_spin.value(),
            "press_data": self.press_data_edit.text().strip(),
            "remark": self.remark_edit.toPlainText().strip(),
            "work_stroke": self.work_stroke_spin.value(),
            "effective_stroke": self.effective_stroke_spin.value(),
            "fill_coeff_test": self.fill_coeff_test_spin.value(),
            "lab_water_cut": self.lab_water_cut_edit.text().strip(),
            "reported_water": self.reported_water_edit.text().strip(),
            "fill_coeff_liquid": self.fill_coeff_liquid_spin.value(),
            "last_tubing_time": self.last_tubing_time_edit.text().strip(),
            "pump_diameter": self.pump_diameter_edit.text().strip(),
            "block": self.block_edit.text().strip(),
            "transformer": self.transformer_edit.text().strip(),
            "well_times": self.well_times_spin.value()
        }

# -------- 简易表格模型 --------
class SimpleTableModel(QAbstractTableModel):
    def __init__(self, headers, rows):
        super().__init__()
        self.headers = headers
        self.rows = rows
    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if role == Qt.DisplayRole:
            return str(self.rows[row][col])  # 显示内容转为字符串
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter  # 👈 所有单元格居中显示
        return None

    def headerData(self, section, orient, role=Qt.DisplayRole):
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
        self.act_export = QAction("导出报表", self)  # 修改按钮文本为通用报表
        self.toolbar.addAction(self.act_export)
        self.act_export.triggered.connect(self._on_export_reports)

        # —— 新增导入公式按钮 ——
        self.act_import_formula = QAction("导入公式", self)
        self.toolbar.addAction(self.act_import_formula)
        self.act_import_formula.triggered.connect(self._on_import_formula)

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
        splitter.setSizes([350, 750])  # 根据需要可调整，单位为像素
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(splitter)

        self._current_level = None
        self._current_id = None
        self._daily_reports = []

        self._build_tree()

    #添加公式
    def _on_import_formula(self):
        dlg = FormulaImportDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            # 获取表格数据（此处可根据实际需求处理数据，如保存到数据库或应用到公式）
            table_data = dlg.get_table_data()
            # 示例：显示导入成功信息
            QMessageBox.information(
                self,
                "导入成功",
                f"已导入 {len(table_data)} 行公式数据\n可在油报公式管理中使用"
            )

    def _on_export_reports(self):
        dlg = ExportDialog(self)
        dlg.exec_()

    # ---- 构建树 ----
    def _build_tree(self):
        model = QStandardItemModel()
        root_item = model.invisibleRootItem()

        # —— 添加可见根节点标题 ——
        it_root = QStandardItem("报表管理")
        it_root.setEditable(False)
        it_root.setData(("root", None), Qt.UserRole + 1)
        root_item.appendRow(it_root)

        # —— 构建新的树结构 ——
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
                    it_room.setData(("room", room.id), Qt.UserRole + 1)
                    it_team.appendRow(it_room)

                    # 获取当前房间下的所有报
                    for bao in list_children("room", room.id):
                        it_bao = QStandardItem(f"报 | {bao.bao_typeid}")
                        it_bao.setData(("bao", bao.id), Qt.UserRole + 1)
                        it_room.appendRow(it_bao)

                        # 根据报的类型决定子节点类型
                        if "水报" in bao.bao_typeid:
                            # 水报的子节点是井
                            for well in list_children("bao", bao.id):
                                it_well = QStandardItem(f"井 | {well.well_code}")
                                it_well.setData(("well", well.id), Qt.UserRole + 1)
                                it_bao.appendRow(it_well)
                        elif "油报" in bao.bao_typeid:
                            # 油报的子节点是平台 - 修改这里
                            for platform in list_children("bao", bao.id):
                                it_platform = QStandardItem(f"平台 | {platform.platformer_id}")
                                # 修改这里，使用"platform"作为类型
                                it_platform.setData(("platform", platform.id), Qt.UserRole + 1)
                                it_bao.appendRow(it_platform)

                                # 平台的子节点是井
                                for well in list_children("platform", platform.id):  # 修改这里，使用"platform"
                                    it_well = QStandardItem(f"井 | {well.well_code}")
                                    it_well.setData(("well", well.id), Qt.UserRole + 1)
                                    it_platform.appendRow(it_well)

        self.tree.setModel(model)
        self.tree.expandAll()

    # ---- 判断油井水井 ----
    def is_oil_well(self, well_id: int) -> bool:
        with DBSession() as db:
            well = db.get(Well, well_id)
            if not well:
                return False  # 默认按水井处理，防止 None 报错

            if well.platform and well.platform.bao:
                bao_typeid = getattr(well.platform.bao, "bao_typeid", "")
            elif well.bao:
                bao_typeid = getattr(well.bao, "bao_typeid", "")
            else:
                bao_typeid = ""

            return "油报" in bao_typeid

    # ---- 树节点点击 ----
    def _on_tree_clicked(self, index):
        level, obj_id = index.data(Qt.UserRole + 1)
        self._current_level, self._current_id = level, obj_id

        rows, headers = [], []

        if level is None:
            return

        try:
            if level == "well":
                is_oil = self.is_oil_well(obj_id)  # 用新函数替代旧逻辑

                reports = list_children("well", obj_id)
                self._daily_reports = reports

                if is_oil:
                    print(f"当前处理油井日报，共有 {len(reports)} 条")

                    headers = [
                        "平台", "日期", "井号", "生产时间(h)", "A2冲程", "A2冲次",
                        "套压(MPa)", "油压(MPa)", "回压(MPa)", "时间标记","合量斗数", "憋压(MPa)", "备注",
                        "功图冲次", "有效排液冲程", "充满系数",
                        "化验含水(%)", "上报含水(%)",
                        "充满系数液量", "上次动管柱时间", "泵径", "区块", "变压器",
                        "液量/斗数", "和", "液量1", "分产系数", "A2(24h)液量", "液量2", "油量", "波动范围",
                        "停产时间", "理论排量-液量差", "理论排量", "K值",
                        "日产液", "日产油", "井次", "时间", "产油(累计)"
                    ]

                    rows = [
                        (
                            fmt(r.platform),  # 平台
                            fmt(r.create_time),  # 日期
                            fmt(r.well_code),  # 井号
                            fmt(r.prod_hours),  # 生产时间(h)
                            fmt(r.a2_stroke),  # A2冲程
                            fmt(r.a2_frequency),  # A2冲次
                            fmt(r.casing_pressure),  # 套压(MPa)
                            fmt(r.oil_pressure),  # 油压(MPa)
                            fmt(r.back_pressure),  # 回压(MPa)
                            fmt(r.time_sign),  # 时间标记
                            fmt(r.total_bucket),  # 合量斗数
                            fmt(r.press_data),  # 憋压(MPa) — 如果你这里用的是憋压，字段名称需确认
                            fmt(r.remark),  # 备注

                            fmt(r.work_stroke),  # 功图冲次 (对应work_stroke)
                            fmt(r.effective_stroke),  # 有效排液冲程
                            fmt(r.fill_coeff_test),  # 充满系数 (模型字段为 fill_coeff_test)

                            fmt(r.lab_water_cut),  # 化验含水(%)
                            fmt(r.reported_water),  # 上报含水(%)

                            fmt(r.fill_coeff_liquid),  # 充满系数液量
                            fmt(r.last_tubing_time),  # 上次动管柱时间
                            fmt(r.pump_diameter),  # 泵径
                            fmt(r.block),  # 区块
                            fmt(r.transformer),  # 变压器

                            fmt(r.liquid_per_bucket),  # 液量/斗数
                            fmt(r.sum_value),  # 和
                            fmt(r.liquid1),  # 液量1
                            fmt(r.production_coeff),  # 分产系数
                            fmt(r.a2_24h_liquid),  # A2(24h)液量
                            fmt(r.liquid2),  # 液量2
                            fmt(r.oil_volume),  # 油量
                            fmt(r.fluctuation_range),  # 波动范围

                            fmt(r.shutdown_time),  # 停产时间
                            fmt(r.theory_diff),  # 理论排量-液量差
                            fmt(r.theory_displacement),  # 理论排量
                            fmt(r.k_value),  # K值

                            fmt(r.daily_liquid),  # 日产液
                            fmt(r.daily_oil),  # 日产油
                            fmt(r.well_times),  # 井次
                            fmt(r.production_time),  # 时间
                            fmt(r.total_oil)  # 产油(累计)
                        )
                        for r in reports
                    ]

                else:
                    print(f"当前处理水井日报，共有 {len(reports)} 条")

                    headers = [
                        "日期", "注水方式", "生产时长(h)",
                        "干线压(MPa)", "油压(MPa)", "套压(MPa)", "井口压(MPa)",
                        "计划注水(m³)", "实际注水(m³)", "备注",
                        "计量阶段1", "计量阶段2", "计量阶段3"
                    ]

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

            elif level == "bao":
                # 获取当前报节点所属的计量间（room）的 ID
                index = self.tree.currentIndex()
                item = self.tree.model().itemFromIndex(index)
                parent_item = item.parent() if item else None
                parent_data = parent_item.data(Qt.UserRole + 1) if parent_item else None
                room_id = parent_data[1] if parent_data and parent_data[0] == "room" else None

                # 查找该报对象
                if room_id:
                    bao_list = list_children("room", room_id)
                    bao = next((b for b in bao_list if b.id == obj_id), None)
                else:
                    bao = next((b for b in list_children("bao", None) if b.id == obj_id), None)
                if not bao:
                    QMessageBox.warning(self, "提示", "找不到当前报信息")
                    return
                # 判断是水报还是油报
                if "水报" in bao.bao_typeid:
                    # 水报下的井
                    wells = list_children("bao", obj_id)
                    headers = ["井ID", "井编号"]
                    if not wells:
                        rows = []
                    else:
                        rows = [(w.id, w.well_code) for w in wells]
                elif "油报" in bao.bao_typeid:
                    # 油报下的平台
                    platforms = list_children("bao", obj_id)
                    headers = ["平台ID", "平台编号"]
                    if not platforms:
                        rows = []
                    else:
                        rows = [(p.id, p.platformer_id) for p in platforms]
                else:
                    QMessageBox.warning(self, "提示", f"未知类型的报：{bao.bao_typeid}")
                    return
                # 显示到表格中
                self.table.setModel(SimpleTableModel(headers, rows))
                self.table.resizeColumnsToContents()
                self.table.setModel(SimpleTableModel(headers, rows))
                self.table.resizeColumnsToContents()

            elif level == "platform":
                # 显示平台下的井
                wells = list_children("platform", obj_id)

                if not wells:
                    headers = ["井ID", "井编号"]
                    rows = []
                else:
                    headers = ["井ID", "井编号"]
                    rows = [(w.id, w.well_code) for w in wells]
            elif level == "root":
                children = list_root()
                headers = ["ID", "作业区名称"]
                rows = [(c.area_id, c.area_name) for c in children]
            else:
                # 其他节点类型（作业区、班组、房间）显示下一级子节点
                children = list_children(level, obj_id)

                if not children:
                    headers = ["ID", "名称/编号"]
                    rows = []
                else:
                    map_func = {
                        "area": lambda x: (x.team_id, x.team_name),
                        "team": lambda x: (x.id, x.room_no),
                        "room": lambda x: (x.id, x.bao_typeid),
                    }

                    headers = ["ID", "名称/编号"]
                    rows = [map_func[level](c) for c in children]

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理{level}节点时出错: {str(e)}")
            print(f"节点处理错误: {level}, {obj_id}, {str(e)}")
            return

        # 显示数据到表格
        self.table.setModel(SimpleTableModel(headers, rows))
        self.table.resizeColumnsToContents()
        self.table.setModel(SimpleTableModel(headers, rows))
        self.table.resizeColumnsToContents()
        # 添加调试信息
        print(f"加载{level}节点数据，共{len(rows)}条记录")

    # ---- 删除当前节点 ----
    def _delete_current(self):
        if not self._current_level:
            return

        # 确认对话框
        if QMessageBox.question(
                self, "确认", "级联删除当前节点及其所有下级？",
                QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.No:
            return

        try:
            # 根据当前节点类型调用不同的删除逻辑
            if self._current_level == "bao":
                # 报节点
                delete_entity("bao", self._current_id)
            elif self._current_level == "platformer":
                # 平台节点
                delete_entity("platformer", self._current_id)
            else:
                # 原有节点类型（作业区、注采班、计量间、井）
                delete_entity(self._current_level, self._current_id)

            QMessageBox.information(self, "完成", "已删除")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

        # 刷新树和表格
        self._build_tree()
        self.table.setModel(SimpleTableModel([], []))

    #添加节点
    def _add_current(self):
        if not self._current_level:
            QMessageBox.warning(self, "错误", "请先选择一个节点")
            return

        try:
            if self._current_level == "root":
                text, ok = QInputDialog.getText(self, "新建作业区", "请输入作业区名称:")
                if ok and text:
                    area_name = text.strip()
                    from database.water_report_dao import upsert_work_area
                    upsert_work_area(area_name)
                    QMessageBox.information(self, "提示", f"作业区“{area_name}”创建成功")

            elif self._current_level == "area":
                # 创建注采班
                text, ok = QInputDialog.getText(self, "新建班组", "请输入班组名称:")
                if ok and text:
                    team_name = text.strip()
                    team_no, ok2 = QInputDialog.getInt(self, "编号", "请输入班组编号:")
                    if ok2:
                        from database.water_report_dao import upsert_prod_team
                        upsert_prod_team(self._current_id, team_no=team_no, team_name=team_name)

            elif self._current_level == "team":
                # 创建计量间
                text, ok = QInputDialog.getText(self, "新建计量间", "请输入计量间号:")
                if ok and text:
                    room_no = text.strip()
                    from database.water_report_dao import upsert_meter_room
                    upsert_meter_room(self._current_id, room_no=room_no)

            elif self._current_level == "room":
                # 创建计量间下的报
                items = ["水报", "油报"]
                item, ok = QInputDialog.getItem(self, "选择报类型", "请选择报类型:", items, 0, False)
                if ok and item:
                    from database.water_report_dao import upsert_bao
                    # 确保使用bao_type参数
                    upsert_bao(self._current_id, bao_type=item)

            elif self._current_level == "bao":
                from database.db_schema import Bao
                # 获取当前报的类型信息
                with DBSession() as db:
                    current_bao = db.get(Bao, self._current_id)

                if not current_bao:
                    QMessageBox.warning(self, "错误", "找不到当前报信息")
                    return

                elif "水报" in current_bao.bao_typeid:
                    text, ok = QInputDialog.getText(self, "新建井", "请输入井编号:")
                    if ok and text:
                        well_code = text.strip()
                        from database.water_report_dao import upsert_well, upsert_daily_report
                        from datetime import date
                        try:
                            well_id = upsert_well(
                                well_code=well_code,
                                bao_type="水报",
                                bao_id=self._current_id
                            )
                            rpt_dict = {
                                "report_date": date.today(),
                                "injection_mode": "",  # 可设默认值
                                "prod_hours": None,
                                "trunk_pressure": None,
                                "oil_pressure": None,
                                "casing_pressure": None,
                                "wellhead_pressure": None,
                                "plan_inject": None,
                                "actual_inject": None,
                                "remark": "",
                                "meter_stage1": None,
                                "meter_stage2": None,
                                "meter_stage3": None,
                            }

                            upsert_daily_report(well_id, rpt_dict)
                            QMessageBox.information(self, "成功", f"添加井成功")
                            self._on_tree_clicked(self.tree.currentIndex())
                        except Exception as e:
                            QMessageBox.warning(self, "失败", str(e))


                elif "油报" in current_bao.bao_typeid:

                    text, ok = QInputDialog.getText(self, "新建平台", "请输入平台编号:")
                    if ok and text:
                        platform_no = text.strip()
                        from database.water_report_dao import upsert_platformer, upsert_well, upsert_oil_report
                        from datetime import date
                        try:
                            platform_id = upsert_platformer(bao_id=self._current_id, platform_name=platform_no)

                            # 查询平台名称，确保有值
                            with DBSession() as db:
                                platform = db.get(Platformer, platform_id)
                                if platform:
                                    platform_name = platform.platformer_id  # 或你想显示的字段
                                else:
                                    platform_name = platform_no  # 兜底，防止查不到

                            # # 创建平台下的井
                            # text, ok = QInputDialog.getText(self, "新建井", "请输入平台下井编号:")
                            # if ok and text:
                            #     well_code = text.strip()
                            #     well_id = upsert_well(
                            #         well_code=well_code,
                            #         bao_type="油报",
                            #         platform_id=platform_id
                            #     )
                            #
                            #     rpt_dict = {
                            #         "create_time": date.today(),
                            #         "platform": platform_no,
                            #         "well_code": well_code,
                            #         "prod_hours": None,
                            #         "a2_stroke": None,
                            #         "a2_frequency": None,
                            #         # 其他字段留空或补默认值
                            #         "casing_pressure": None,
                            #         "oil_pressure": None,
                            #         "back_pressure": None,
                            #         "remark": "",
                            #     }
                            #     upsert_oil_report(well_id, rpt_dict)
                            #
                            # self._on_tree_clicked(self.tree.currentIndex())
                        except Exception as e:
                            QMessageBox.warning(self, "失败", str(e))

            elif self._current_level == "platform":
                text, ok = QInputDialog.getText(self, "新建井", "请输入井编号:")
                if ok and text:
                    well_code = text.strip()
                    from database.water_report_dao import upsert_well, upsert_oil_report
                    from datetime import date
                    try:
                        # 查询平台名称
                        with DBSession() as db:
                            platform = db.get(Platformer, self._current_id)
                            platform_name = platform.platformer_id if platform else ""
                        well_id = upsert_well(
                            well_code=well_code,
                            bao_type="油报",
                            platform_id=self._current_id
                        )
                        rpt_dict = {
                            "create_time": date.today(),
                            "platform": platform_name,
                            "well_code": well_code,
                            "prod_hours": None,
                            "a2_stroke": None,
                            "a2_frequency": None,
                            "casing_pressure": None,
                            "oil_pressure": None,
                            "back_pressure": None,
                            "remark": "",
                        }
                        upsert_oil_report(well_id, rpt_dict)
                        QMessageBox.information(self, "成功", f"添加井成功")
                        self._on_tree_clicked(self.tree.currentIndex())
                    except Exception as e:
                        QMessageBox.warning(self, "失败", str(e))

            elif self._current_level == "well":
                from database.db_schema import Well, Bao
                with DBSession() as db:
                    # 获取当前井对象
                    well = db.get(Well, self._current_id)
                    if not well:
                        QMessageBox.warning(self, "错误", "找不到当前井信息")
                        return
                    # 获取所属报类型
                    bao = db.get(Bao, well.bao_id)
                    if not bao:
                        QMessageBox.warning(self, "错误", "找不到所属报信息")
                        return
                    # 判断报类型：弹出不同对话框
                    if "水报" in bao.bao_typeid:
                        dlg = DailyReportDialog(self)
                    elif "油报" in bao.bao_typeid:
                        well = db.get(Well, self._current_id)
                        dlg = OilReportDialog(self, platform=well.platform.platformer_id, well_code=well.well_code)
                    else:
                        QMessageBox.warning(self, "错误", "无法判断报类型（非水报/油报）")
                        return
                    # 如果用户点击了确定，保存日报
                    if dlg.exec_() == QDialog.Accepted:
                        rpt = dlg.get_data()

                        if "水报" in bao.bao_typeid:
                            from database.water_report_dao import upsert_daily_report
                            upsert_daily_report(self._current_id, rpt)
                            QMessageBox.information(self, "提示", "日报添加成功")
                        elif "油报" in bao.bao_typeid:
                            from database.water_report_dao import upsert_oil_report
                            upsert_oil_report(self._current_id, rpt)
                            QMessageBox.information(self, "提示", "日报添加成功")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")
            print(f"异常详细信息: {traceback.format_exc()}")  # 打印完整堆栈信息

        # 刷新树和表格
        self._build_tree()
        self.table.setModel(SimpleTableModel([], []))

    def _on_table_context_menu(self, pos):
        try:
            if self._current_level != "well":
                return

            idx = self.table.indexAt(pos)
            if not idx.isValid():
                return

            menu = QMenu(self.table)
            edit_act = menu.addAction("修改报表")
            delete_act = menu.addAction("删除报表")
            act = menu.exec_(self.table.viewport().mapToGlobal(pos))
            if not act:
                return

            row = idx.row()
            rpt_obj = self._daily_reports[row]

            if act == edit_act:
                from src.database.db_schema import DailyReport, OilWellDatas
                if isinstance(rpt_obj, DailyReport):
                    dlg = DailyReportDialog(self, data=rpt_obj)
                elif isinstance(rpt_obj, OilWellDatas):
                    # 避免懒加载，直接用外键字段或传入必要信息
                    platform_id = getattr(rpt_obj, "platform", "")
                    well_code = getattr(rpt_obj, "well_code", "")
                    dlg = OilReportDialog(self, platform=platform_id, well_code=well_code, data=rpt_obj)
                    if hasattr(dlg, "set_data"):
                        dlg.set_data(rpt_obj)
                else:
                    QMessageBox.warning(self, "错误", "未知报表类型")
                    return

                if dlg.exec_() == QDialog.Accepted:
                    new_data = dlg.get_data()
                    if isinstance(rpt_obj, DailyReport):
                        from database.water_report_dao import upsert_daily_report
                        upsert_daily_report(self._current_id, new_data)
                    else:
                        from database.water_report_dao import upsert_oil_report
                        upsert_oil_report(self._current_id, new_data)
                    self._on_tree_clicked(self.tree.currentIndex())

            elif act == delete_act:
                delete_entity("report", getattr(rpt_obj, "report_id", getattr(rpt_obj, "id", None)))
                QMessageBox.information(self, "完成", "已删除")
                self._on_tree_clicked(self.tree.currentIndex())

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"操作异常:\n{e}")


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
        it_root.setEditable(False)  # 根节点通常不允许编辑
        it_root.setData((None, None), Qt.UserRole + 1)
        root_item.appendRow(it_root)

        it_team = QStandardItem()

        for area in list_root():
            if area.area_name == self.permission_list[1]:
                self.area_id = area.area_id
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

        if level is None:
            return

        try:
            if level == "well":
                # 显示井的日报数据
                reports = list_children("well", obj_id)
                self._daily_reports = reports

                headers = [
                    "日期", "注水方式", "生产时长(h)",
                    "干线压(MPa)", "油压(MPa)", "套压(MPa)", "井口压(MPa)",
                    "计划注水(m³)", "实际注水(m³)", "备注",
                    "计量阶段1", "计量阶段2", "计量阶段3"
                ]

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

            elif level == "bao":
                # 显示报下的内容（水报/油报）
                # 修改这里：移除child_type参数
                bao_list = list_children("room", obj_id)
                bao = next((b for b in bao_list if b.id == obj_id), None)

                if not bao:
                    return

                if "水报" in bao.bao_typeid:
                    # 水报下的井
                    # 修改这里：移除child_type参数
                    wells = list_children("bao", obj_id)
                    headers = ["井ID", "井编号"]
                    rows = [(w.id, w.well_code) for w in wells]  # 使用w.id而非w.well_id
                elif "油报" in bao.bao_typeid:
                    # 油报下的平台
                    # 修改这里：移除child_type参数
                    platforms = list_children("bao", obj_id)
                    headers = ["平台ID", "平台编号"]
                    rows = [(p.id, p.platformer_id) for p in platforms]

            elif level == "platform":
                # 显示平台下的井
                # 修改这里：移除child_type参数
                wells = list_children("platformer", obj_id)
                headers = ["井ID", "井编号"]
                rows = [(w.id, w.well_code) for w in wells]  # 使用w.id而非w.well_id

            else:
                # 其他节点类型（作业区、班组、房间）显示下一级子节点
                # 修改这里：移除child_type参数
                children = list_children(level, obj_id)

                map_func = {
                    "area": lambda x: (x.id, x.team_name),
                    "team": lambda x: (x.id, x.room_no),
                    "room": lambda x: (x.id, x.bao_typeid),
                }

                headers = ["ID", "名称/编号"]
                rows = [map_func[level](c) for c in children]

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理{level}节点时出错: {str(e)}")
            print(f"节点处理错误: {level}, {obj_id}, {str(e)}")
            return

        self.table.setModel(SimpleTableModel(headers, rows))

    # ---- 删除当前节点 ----
    def _delete_current(self):
        if not self._current_level:
            return

        # 确认对话框
        if QMessageBox.question(
                self, "确认", "级联删除当前节点及其所有下级？",
                QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.No:
            return

        try:
            # 根据当前节点类型调用不同的删除逻辑
            if self._current_level == "bao":
                # 报节点（水报/油报）
                delete_entity("bao", self._current_id)
            elif self._current_level == "platformer":
                # 平台节点
                delete_entity("platformer", self._current_id)
            elif self._current_level == "well":
                # 井节点
                # 先删除该井的所有日报
                delete_entity("report", parent_id=self._current_id)
                # 再删除井本身
                delete_entity("well", self._current_id)
            else:
                # 其他节点类型（作业区、班组、房间）
                delete_entity(self._current_level, self._current_id)

            QMessageBox.information(self, "完成", "已删除")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

        # 刷新树和表格
        self._build_tree()
        self.table.setModel(SimpleTableModel([], []))

    def _add_current(self):
        if not self._current_level:
            QMessageBox.warning(self, "错误", "请先选择一个节点")
            return

        try:
            if self._current_level == "area":
                # 创建注采班
                text, ok = QInputDialog.getText(self, "新建班组", "请输入班组名称:")
                if ok and text:
                    team_name = text.strip()
                    team_no, ok2 = QInputDialog.getInt(self, "编号", "请输入班组编号:")
                    if ok2:
                        from database.water_report_dao import upsert_prod_team
                        upsert_prod_team(self._current_id, team_no=team_no, team_name=team_name)
                        QMessageBox.information(self, "成功", "班组创建成功")
                        self._build_tree()  # 刷新树视图

            elif self._current_level == "team":
                # 创建计量间
                text, ok = QInputDialog.getText(self, "新建计量间", "请输入计量间号:")
                if ok and text:
                    room_no = text.strip()
                    from database.water_report_dao import upsert_meter_room
                    upsert_meter_room(self._current_id, room_no=room_no)
                    QMessageBox.information(self, "成功", "计量间创建成功")
                    self._build_tree()  # 刷新树视图

            elif self._current_level == "room":
                # 创建计量间下的报
                items = ["水报", "油报"]
                item, ok = QInputDialog.getItem(self, "选择报类型", "请选择报类型:", items, 0, False)
                if ok and item:
                    from database.water_report_dao import upsert_bao
                    upsert_bao(self._current_id, bao_type=item)
                    QMessageBox.information(self, "成功", f"{item}创建成功")
                    self._build_tree()  # 刷新树视图

            elif self._current_level == "bao":
                # 获取当前报的类型信息
                bao_list = list_children("room", self._current_id)
                current_bao = next((b for b in bao_list if b.id == self._current_id), None)

                if not current_bao:
                    QMessageBox.warning(self, "错误", "找不到当前报信息")
                    return

                if "水报" in current_bao.bao_typeid:
                    # 水报下创建井
                    text, ok = QInputDialog.getText(self, "新建井", "请输入井编号:")
                    if ok and text:
                        well_code = text.strip()
                        from database.water_report_dao import upsert_well
                        well_id = upsert_well(bao_id=self._current_id, well_code=well_code)
                        if well_id:
                            QMessageBox.information(self, "成功", "井创建成功")
                            self._build_tree()  # 刷新树视图
                            # 如果当前选中的是该报节点，刷新表格
                            if self._current_level == "bao" and self._current_id == current_bao.id:
                                self._on_tree_clicked(self.tree.currentIndex())
                        else:
                            QMessageBox.warning(self, "失败", "井创建失败")
                elif "油报" in current_bao.bao_typeid:
                    # 油报下创建平台
                    text, ok = QInputDialog.getText(self, "新建平台", "请输入平台编号:")
                    if ok and text:
                        platform_no = text.strip()
                        from database.water_report_dao import upsert_platformer
                        platform_id = upsert_platformer(bao_id=self._current_id, platform_no=platform_no)
                        if platform_id:
                            QMessageBox.information(self, "成功", "平台创建成功")
                            self._build_tree()  # 刷新树视图
                            # 如果当前选中的是该报节点，刷新表格
                            if self._current_level == "bao" and self._current_id == current_bao.id:
                                self._on_tree_clicked(self.tree.currentIndex())
                        else:
                            QMessageBox.warning(self, "失败", "平台创建失败")

            elif self._current_level == "platform":  # 修改为"platform"以匹配树节点类型
                # 平台下创建井
                text, ok = QInputDialog.getText(self, "新建井", "请输入井编号:")
                if ok and text:
                    well_code = text.strip()
                    from database.water_report_dao import upsert_well
                    well_id = upsert_well(platformer_id=self._current_id, well_code=well_code)
                    if well_id:
                        QMessageBox.information(self, "成功", "井创建成功")
                        self._build_tree()  # 刷新树视图
                        # 如果当前选中的是该平台节点，刷新表格
                        if self._current_level == "platform":
                            self._on_tree_clicked(self.tree.currentIndex())
                    else:
                        QMessageBox.warning(self, "失败", "井创建失败")

            elif self._current_level == "well":
                # 创建日报
                dlg = DailyReportDialog(self)
                if dlg.exec_() == QDialog.Accepted:
                    rpt = dlg.get_data()
                    report_id = upsert_daily_report(self._current_id, rpt)
                    if report_id:
                        QMessageBox.information(self, "成功", "日报创建成功")
                        # 如果当前选中的是该井节点，刷新表格
                        if self._current_level == "well":
                            self._on_tree_clicked(self.tree.currentIndex())
                    else:
                        QMessageBox.warning(self, "失败", "日报创建失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")
            print(f"异常详细信息: {traceback.format_exc()}")  # 打印完整堆栈信息

        # 刷新树和表格
        # self._build_tree()  # 已在每个操作成功后单独调用
        # self.table.setModel(SimpleTableModel([], []))

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
        elif act == delete_act:
            row = idx.row()
            rpt_obj = self._daily_reports[row]
            # 恢复原有调用方式
            delete_entity("report", rpt_obj.report_id)
            QMessageBox.information(self, "完成", "已删除")
            self._on_tree_clicked(self.tree.currentIndex())

# ---- 运行 ----
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AdminPage()

    win.show()

    sys.exit(app.exec_())
