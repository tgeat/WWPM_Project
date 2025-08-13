from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QDialogButtonBox,
    QDialog,
    QComboBox,
    QMenu,
    QLineEdit,
)
from PyQt5.QtCore import Qt


class FormulaImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入公式 - 表格编辑")
        self.resize(1000, 600)

        self.COLUMN_WIDTHS = {0: 210, 1: 60, "default": 200}

        main_layout = QVBoxLayout(self)

        self.table = QTableWidget(16, 6)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setStretchLastSection(True)
        self._populate_first_two_columns()
        self._adjust_column_widths()

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        self.combo_options = [
            "",
            "+",
            "-",
            "*",
            "/",
            "(",
            ")",
            "平台",
            "日期",
            "井号",
            "生产时间",
            "A2冲程",
            "A2冲次",
            "套压",
            "油压",
            "回压",
            "时间标记",
            "合量斗数",
            "憋压数据",
            "备注",
            "功图冲次",
            "有效排液冲程",
            "充满系数",
            "化验含水",
            "上报含水",
            "充满系数液量",
            "上次动管柱时间",
            "泵径",
            "区块",
            "变压器",
        ]

        self._setup_comboboxes()

        main_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("增加行")
        self.add_row_btn.clicked.connect(self.add_row)
        btn_layout.addWidget(self.add_row_btn)

        self.add_col_btn = QPushButton("增加列")
        self.add_col_btn.clicked.connect(self.add_col)
        btn_layout.addWidget(self.add_col_btn)

        self.import_btn = QPushButton("导出")
        btn_layout.addWidget(self.import_btn)

        main_layout.addLayout(btn_layout)

    def get_import_button(self) -> QPushButton:
        return self.import_btn

    def _populate_first_two_columns(self):
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
            "产油",
        ]

        max_rows = max(len(first_column_data), 16)
        if self.table.rowCount() < max_rows:
            self.table.setRowCount(max_rows)

        for row, text in enumerate(first_column_data):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item)

        for row in range(max_rows):
            item = QTableWidgetItem("=")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, item)

    def _adjust_column_widths(self):
        for col in range(self.table.columnCount()):
            width = self.COLUMN_WIDTHS.get(col, self.COLUMN_WIDTHS["default"])
            self.table.setColumnWidth(col, width)
        self.table.viewport().update()
        self.table.updateGeometry()

    def _show_context_menu(self, position):
        index = self.table.indexAt(position)
        if index.isValid() and index.column() == 0:
            menu = QMenu()
            edit_action = menu.addAction("修改内容")
            action = menu.exec_(self.table.viewport().mapToGlobal(position))
            if action == edit_action:
                self._edit_cell_text(index.row(), index.column())

    def _edit_cell_text(self, row, col):
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
            self.table.setColumnWidth(0, max(self.COLUMN_WIDTHS[0], self.table.columnWidth(0)))

    def _setup_comboboxes(self):
        for row in range(self.table.rowCount()):
            for col in range(2, self.table.columnCount()):
                self._set_combobox_for_cell(row, col)

    def _set_combobox_for_cell(self, row, col):
        combo = QComboBox()
        combo.addItems(self.combo_options)
        combo.setCurrentIndex(0)
        combo.setEditable(True)
        combo.lineEdit().setAlignment(Qt.AlignCenter)
        combo.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        combo.setStyleSheet(
            """
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
            """
        )
        self.table.setCellWidget(row, col, combo)

    def add_row(self):
        current_row = self.table.rowCount()
        self.table.insertRow(current_row)
        item1 = QTableWidgetItem("")
        item1.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(current_row, 0, item1)

        item2 = QTableWidgetItem("=")
        item2.setTextAlignment(Qt.AlignCenter)
        item2.setFlags(item2.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(current_row, 1, item2)

        for col in range(2, self.table.columnCount()):
            self._set_combobox_for_cell(current_row, col)
        self._adjust_column_widths()

    def add_col(self):
        current_col = self.table.columnCount()
        self.table.insertColumn(current_col)
        width = self.COLUMN_WIDTHS["default"]
        self.table.setColumnWidth(current_col, width)
        for row in range(self.table.rowCount()):
            self._set_combobox_for_cell(row, current_col)
        self._adjust_column_widths()

    def get_table_data(self):
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                if col < 2:
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                else:
                    combo = self.table.cellWidget(row, col)
                    row_data.append(combo.currentText() if combo else "")
            data.append(row_data)
        return data
