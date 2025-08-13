import sys
import pymysql
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout,
                             QDialogButtonBox, QDialog, QApplication, QComboBox, QMenu, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt


class FormulaImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入公式 - 表格编辑")
        self.resize(1000, 600)

        # 定义固定列宽配置
        self.COLUMN_WIDTHS = {
            0: 210,  # 第一列宽度
            1: 60,  # 第二列宽度
            "default": 200  # 其余列宽度
        }

        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建表格（16行6列）
        self.table = QTableWidget(16, 6)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setStretchLastSection(True)
        self._populate_first_two_columns()

        self._adjust_column_widths()

        # 设置右键菜单
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # 初始化下拉框选项
        self.combo_options = ['', '+', '-', '*', '/', '(', ')', '平台', '日期', '井号',
                              '生产时间', 'A2冲程', 'A2冲次', '套压',
                              '油压', '回压', '时间标记', '合量斗数', '憋压数据',
                              '备注', '功图冲次', '有效排液冲程', '充满系数',
                              '化验含水', '上报含水', '充满系数液量', '上次动管柱时间',
                              '泵径', '区块', '变压器']

        # 为除前两列外的单元格设置下拉框
        self._setup_comboboxes()

        main_layout.addWidget(self.table)

        # 按钮布局
        btn_layout = QHBoxLayout()

        self.add_row_btn = QPushButton("增加行")
        self.add_row_btn.clicked.connect(self.add_row)
        btn_layout.addWidget(self.add_row_btn)

        self.add_col_btn = QPushButton("增加列")
        self.add_col_btn.clicked.connect(self.add_col)
        btn_layout.addWidget(self.add_col_btn)

        self.import_btn = QPushButton("导出")
        self.import_btn.clicked.connect(self.import_to_mysql)
        btn_layout.addWidget(self.import_btn)

        main_layout.addLayout(btn_layout)

    def _populate_first_two_columns(self):
        """填充前两列数据"""
        first_column_data = [
            "液量/斗数（功图）",
            "液量/斗数（60/流量计）",
            "和",
            "液量",
            "分产系数",
            "A2(24h)液量",
            "液量（资料员）",
            "油量",
            "波动范围",
            "停产时间",
            "理论排量-液量差值",
            "理论排量",
            "日产液",
            "日产油",
            "时间",
            "产油"
        ]

        max_rows = max(len(first_column_data), 16)
        if self.table.rowCount() < max_rows:
            self.table.setRowCount(max_rows)

        # 填充第一列
        for row, text in enumerate(first_column_data):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item)

        # 填充第二列（"="）
        for row in range(max_rows):
            item = QTableWidgetItem("=")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, item)

    def _adjust_column_widths(self):
        """严格按照固定值设置列宽，禁用自动调整"""
        for col in range(self.table.columnCount()):
            width = self.COLUMN_WIDTHS.get(col, self.COLUMN_WIDTHS["default"])
            self.table.setColumnWidth(col, width)

        # 强制布局更新（关键修改）
        self.table.viewport().update()
        self.table.updateGeometry()

    def _show_context_menu(self, position):
        """显示右键菜单"""
        index = self.table.indexAt(position)
        if index.isValid() and index.column() == 0:  # 只在第一列显示右键菜单
            menu = QMenu()
            edit_action = menu.addAction("修改内容")
            action = menu.exec_(self.table.viewport().mapToGlobal(position))

            if action == edit_action:
                self._edit_cell_text(index.row(), index.column())

    def _edit_cell_text(self, row, col):
        """编辑单元格文本"""
        current_text = self.table.item(row, col).text()
        dialog = QDialog(self)
        dialog.setWindowTitle("修改内容")
        dialog.resize(300, 100)

        layout = QVBoxLayout(dialog)
        line_edit = QLineEdit(current_text, dialog)
        layout.addWidget(line_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_():
            new_text = line_edit.text()
            self.table.item(row, col).setText(new_text)
            # 更新列宽以适应新内容（仅第一列）
            self.table.setColumnWidth(0, max(self.COLUMN_WIDTHS[0], self.table.columnWidth(0)))

    def _setup_comboboxes(self):
        """为除前两列外的单元格设置下拉框"""
        for row in range(self.table.rowCount()):
            for col in range(2, self.table.columnCount()):
                self._set_combobox_for_cell(row, col)

    def _set_combobox_for_cell(self, row, col):
        """为指定单元格设置下拉框"""
        combo = QComboBox()
        combo.addItems(self.combo_options)
        combo.setCurrentIndex(0)  # 默认空选项
        combo.setEditable(True)  # 允许手动输入
        combo.lineEdit().setAlignment(Qt.AlignCenter)  # 文本居中

        # 优化下拉框行为：下拉时不调整列宽
        combo.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)

        # 设置下拉框的样式
        combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #AAAAAA;
                border-radius: 2px;
                padding: 1px 18px 1px 3px;
                min-width: 6em;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)

        # 将下拉框与单元格关联
        self.table.setCellWidget(row, col, combo)

    def add_row(self):
        """增加一行"""
        current_row = self.table.rowCount()
        self.table.insertRow(current_row)

        # 第一列设为空普通单元格
        item1 = QTableWidgetItem("")
        item1.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(current_row, 0, item1)

        # 第二列设为"="（只读）
        item2 = QTableWidgetItem("=")
        item2.setTextAlignment(Qt.AlignCenter)
        item2.setFlags(item2.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(current_row, 1, item2)

        # 其余列设为下拉框
        for col in range(2, self.table.columnCount()):
            self._set_combobox_for_cell(current_row, col)

        # 强制刷新列宽（关键修改）
        self._adjust_column_widths()

    def add_col(self):
        """增加一列下拉框"""
        current_col = self.table.columnCount()
        self.table.insertColumn(current_col)

        # 使用预设宽度而非动态计算
        width = self.COLUMN_WIDTHS["default"]
        self.table.setColumnWidth(current_col, width)

        # 为新列所有行设置下拉框
        for row in range(self.table.rowCount()):
            self._set_combobox_for_cell(row, current_col)

        self._adjust_column_widths()

    def get_table_data(self):
        """获取表格数据（二维列表）"""
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                if col < 2:  # 前两列是普通单元格
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                else:  # 其余列是下拉框
                    combo = self.table.cellWidget(row, col)
                    row_data.append(combo.currentText() if combo else "")
            data.append(row_data)
        return data

    def import_to_mysql(self):
        """将表格内容导出到MySQL数据库，增加重复判断逻辑"""
        try:
            # 从DB_URI解析连接参数
            db_uri = "mysql+pymysql://root:112224@127.0.0.1:3306/water_report?charset=utf8mb4"

            import re
            match = re.match(r'mysql\+pymysql://(\w+):(\w+)@([\d\.]+):(\d+)/(\w+)\?charset=(\w+)', db_uri)
            if not match:
                raise ValueError("无效的DB_URI格式")

            user, password, host, port, database, charset = match.groups()

            # 连接数据库
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=int(port),
                charset=charset
            )
            cursor = conn.cursor()

            # 1. 查询数据库中已有的公式，构建映射：{左侧: (id, 右侧)}
            existing_formulas = {}  # key: left_part, value: (id, right_part)
            cursor.execute("SELECT id, formula FROM formula_datas")
            for id_, formula in cursor.fetchall():
                if "=" not in formula:
                    continue  # 跳过格式错误的公式
                left_old, right_old = formula.split("=", 1)  # 只按第一个"="拆分
                existing_formulas[left_old] = (id_, right_old)

            # 2. 处理表格中的新公式
            table_data = self.get_table_data()
            to_update = []  # 待更新：(新公式, id)
            to_insert = []  # 待插入：(新公式,)

            for row in table_data:
                left_new = row[0].strip()
                if not left_new:
                    continue  # 跳过左侧为空的行

                right_parts = [cell.strip() for cell in row[2:] if cell.strip()]
                if not right_parts:
                    continue  # 跳过右侧为空的行

                right_new = ''.join(right_parts)
                new_formula = f"{left_new}={right_new}"

                # 3. 与已有公式比对
                if left_new in existing_formulas:
                    existing_id, existing_right = existing_formulas[left_new]
                    if right_new == existing_right:
                        # 重复
                        continue
                    else:
                        # 更新列表
                        to_update.append((new_formula, existing_id))
                else:
                    # 插入列表
                    to_insert.append((new_formula,))

            # 4. 执行更新和插入
            if to_update:
                update_sql = "UPDATE formula_datas SET formula = %s WHERE id = %s"
                cursor.executemany(update_sql, to_update)

            if to_insert:
                insert_sql = "INSERT INTO formula_datas (formula) VALUES (%s)"
                cursor.executemany(insert_sql, to_insert)

            total = len(to_update) + len(to_insert)
            conn.commit()
            cursor.close()
            conn.close()
            # 弹出一个导出成功提示
            QMessageBox.information(
                self,
                "导出成功",
                f"导出完成：共处理 {total} 条公式"
            )
        except Exception as e:
            print(f"数据导出失败: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = FormulaImportDialog()
    dlg.show()
    sys.exit(app.exec_())