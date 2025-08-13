'''import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QLabel, QScrollArea, QVBoxLayout
from PyQt5 import uic

from asserts.ui.storage_oil_view_ui import Ui_Form


class OilStorageView(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        self.ui.label_9.setText(f"{current_date} 油报")

        font = self.ui.label_9.font()
        font.setBold(True)
        font.setPointSize(16)
        self.ui.label_9.setFont(font)
        self.resize(1000, 800)

        # 缩放相关初始化
        self.scale_factor = 1.0
        self.scale_widgets = []
        self.original_font_sizes = {}

        self.collect_scale_widgets()

    def collect_scale_widgets(self):
        """收集左侧滚动区域内所有需要缩放的控件"""
        scroll_area = self.ui.scrollAreaWidgetContents

        labels = scroll_area.findChildren(QLabel)
        line_edits = scroll_area.findChildren(QLineEdit)
        self.scale_widgets = labels + line_edits

        for widget in self.scale_widgets:
            self.original_font_sizes[widget] = widget.font().pointSize()

    def zoom_in(self):
        """放大：增加缩放比例并应用"""
        if self.scale_factor < 3.0:
            self.scale_factor += 0.1
            self.apply_scale()

    def zoom_out(self):
        """缩小：减小缩放比例并应用"""
        if self.scale_factor > 0.5:
            self.scale_factor -= 0.1
            self.apply_scale()

    def apply_scale(self):
        """仅调整字体大小，让布局系统自动处理控件尺寸"""
        for widget in self.scale_widgets:
            original_size = self.original_font_sizes.get(widget, 10)
            new_font_size = int(original_size * self.scale_factor)

            font = widget.font()
            font.setPointSize(new_font_size)
            widget.setFont(font)

        # 强制布局更新
        self.ui.scrollAreaWidgetContents.layout().update()
        self.ui.scrollAreaWidgetContents.adjustSize()

    def get_lineEdit_wellNum(self) -> QLineEdit:
        return self.ui.lineEdit_wellNum

    def get_lineEdit_injectFuc(self) -> QLineEdit:
        return self.ui.lineEdit_injectFuc

    def get_lineEdit_oilPres(self) -> QLineEdit:
        return self.ui.lineEdit_oilPres

    def get_lineEdit_casePres(self) -> QLineEdit:
        return self.ui.lineEdit_casePres

    def get_lineEdit_wellOilPres(self) -> QLineEdit:
        return self.ui.lineEdit_wellOilPres

    def get_lineEdit_10(self) -> QLineEdit:
        return self.ui.lineEdit_10

    def get_lineEdit_firstExecl(self) -> QLineEdit:
        return self.ui.lineEdit_firstExecl

    def get_lineEdit_firstWater(self) -> QLineEdit:
        return self.ui.lineEdit_firstWater

    def get_lineEdit_productLong(self) -> QLineEdit:
        return self.ui.lineEdit_productLong

    def get_lineEdit_mainLinePres(self) -> QLineEdit:
        return self.ui.lineEdit_mainLinePres

    def get_lineEdit_2(self) -> QLineEdit:  # A2冲次
        return self.ui.lineEdit_2

    def get_lineEdit_daliyWater(self) -> QLineEdit:
        return self.ui.lineEdit_daliyWater

    def get_lineEdit_totalWater(self) -> QLineEdit:
        return self.ui.lineEdit_totalWater

    def get_lineEdit_3(self) -> QLineEdit:  # 充满系数
        return self.ui.lineEdit_3

    def get_lineEdit_testWater(self) -> QLineEdit:  # 化验含水
        return self.ui.lineEdit

    def get_lineEdit_4(self) -> QLineEdit:  # 上报含水
        return self.ui.lineEdit_4

    def get_lineEdit_5(self) -> QLineEdit:  # 充满系数液量
        return self.ui.lineEdit_5

    def get_lineEdit_6(self) -> QLineEdit:  # 上次动管柱时间
        return self.ui.lineEdit_6

    def get_lineEdit_7(self) -> QLineEdit:  # 泵径
        return self.ui.lineEdit_7

    def get_lineEdit_8(self) -> QLineEdit:  # 区块
        return self.ui.lineEdit_8

    def get_lineEdit_9(self) -> QLineEdit:  # 变压器
        return self.ui.lineEdit_9

    def get_lineEdit_note(self) -> QLineEdit:  # 备注
        return self.ui.lineEdit_note


if __name__ == "__main__":
    app = QApplication([])
    w = OilStorageView()
    w.show()
    app.exec_()'''

import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QLabel, QScrollArea, QVBoxLayout, QPushButton
from PyQt5 import uic

from asserts.ui.storage_oil_view_ui import Ui_Form


class OilStorageView(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        self.ui.label_9.setText(f"{current_date} 油报")

        font = self.ui.label_9.font()
        font.setBold(True)
        font.setPointSize(16)
        self.ui.label_9.setFont(font)
        self.resize(1000, 800)

        # 缩放相关初始化
        self.scale_factor = 1.0
        self.scale_widgets = []
        self.original_font_sizes = {}

        self.collect_scale_widgets()
        self.bind_zoom_buttons()  # 绑定缩放按钮

    def collect_scale_widgets(self):
        """收集输入数据页和计算结果页所有需要缩放的控件"""
        # 输入数据页面控件
        input_widgets = self.ui.scrollAreaWidgetContents.findChildren(QLabel) + \
                        self.ui.scrollAreaWidgetContents.findChildren(QLineEdit)

        # 计算结果页面控件
        result_widgets = self.ui.result_scroll_widget.findChildren(QLabel) + \
                         self.ui.result_scroll_widget.findChildren(QLineEdit)

        self.scale_widgets = input_widgets + result_widgets

        # 记录原始字体大小
        for widget in self.scale_widgets:
            self.original_font_sizes[widget] = widget.font().pointSize()

    def bind_zoom_buttons(self):
        """绑定所有放大缩小按钮"""
        self.ui.pushButton_add.clicked.connect(self.zoom_in)
        self.ui.pushButton_minus.clicked.connect(self.zoom_out)
        self.ui.pushButton_result_add.clicked.connect(self.zoom_in)
        self.ui.pushButton_result_minus.clicked.connect(self.zoom_out)
        self.ui.pushButton_group1_add.clicked.connect(self.zoom_in)
        self.ui.pushButton_group1_minus.clicked.connect(self.zoom_out)

    def zoom_in(self):
        if self.scale_factor < 3.0:
            self.scale_factor += 0.1
            self.apply_scale()

    def zoom_out(self):
        if self.scale_factor > 0.5:
            self.scale_factor -= 0.1
            self.apply_scale()

    def apply_scale(self):
        for widget in self.scale_widgets:
            original_size = self.original_font_sizes.get(widget, 10)
            new_font_size = int(original_size * self.scale_factor)
            font = widget.font()
            font.setPointSize(new_font_size)
            widget.setFont(font)
        self.ui.scrollAreaWidgetContents.layout().update()
        self.ui.scrollAreaWidgetContents.adjustSize()
        self.ui.result_scroll_widget.layout().update()
        self.ui.result_scroll_widget.adjustSize()

    # ---------------------- 输入数据页控件getter ----------------------
    def get_lineEdit_wellNum(self) -> QLineEdit:
        return self.ui.lineEdit_wellNum

    def get_lineEdit_injectFuc(self) -> QLineEdit:
        return self.ui.lineEdit_injectFuc

    def get_lineEdit_oilPres(self) -> QLineEdit:
        return self.ui.lineEdit_oilPres

    def get_lineEdit_casePres(self) -> QLineEdit:
        return self.ui.lineEdit_casePres

    def get_lineEdit_wellOilPres(self) -> QLineEdit:
        return self.ui.lineEdit_wellOilPres

    def get_lineEdit_10(self) -> QLineEdit:
        return self.ui.lineEdit_10

    def get_lineEdit_firstExecl(self) -> QLineEdit:
        return self.ui.lineEdit_firstExecl

    def get_lineEdit_firstWater(self) -> QLineEdit:
        return self.ui.lineEdit_firstWater

    def get_lineEdit_productLong(self) -> QLineEdit:
        return self.ui.lineEdit_productLong

    def get_lineEdit_mainLinePres(self) -> QLineEdit:
        return self.ui.lineEdit_mainLinePres

    def get_lineEdit_2(self) -> QLineEdit:  # A2冲次
        return self.ui.lineEdit_2

    def get_lineEdit_daliyWater(self) -> QLineEdit:
        return self.ui.lineEdit_daliyWater

    def get_lineEdit_totalWater(self) -> QLineEdit:
        return self.ui.lineEdit_totalWater

    def get_lineEdit_3(self) -> QLineEdit:  # 充满系数
        return self.ui.lineEdit_3

    def get_lineEdit_testWater(self) -> QLineEdit:  # 化验含水
        return self.ui.lineEdit

    def get_lineEdit_4(self) -> QLineEdit:  # 上报含水
        return self.ui.lineEdit_4

    def get_lineEdit_5(self) -> QLineEdit:  # 充满系数液量
        return self.ui.lineEdit_5

    def get_lineEdit_6(self) -> QLineEdit:  # 上次动管柱时间
        return self.ui.lineEdit_6

    def get_lineEdit_7(self) -> QLineEdit:  # 泵径
        return self.ui.lineEdit_7

    def get_lineEdit_8(self) -> QLineEdit:  # 区块
        return self.ui.lineEdit_8

    def get_lineEdit_9(self) -> QLineEdit:  # 变压器
        return self.ui.lineEdit_9

    def get_lineEdit_note(self) -> QLineEdit:  # 备注
        return self.ui.lineEdit_note

    def get_lineEdit_nums(self)->QLineEdit:
        return self.ui.lineEdit_nums

    # ---------------------- 计算结果页控件getter ----------------------
    def get_lineEdit_liquid_bucket(self) -> QLineEdit:
        return self.ui.lineEdit_liquid_bucket

    def get_lineEdit_sum(self) -> QLineEdit:
        return self.ui.lineEdit_sum

    def get_lineEdit_liquid(self) -> QLineEdit:
        return self.ui.lineEdit_liquid

    def get_lineEdit_distribution_coeff(self) -> QLineEdit:
        return self.ui.lineEdit_distribution_coeff

    def get_lineEdit_a2_24h(self) -> QLineEdit:
        return self.ui.lineEdit_a2_24h

    def get_lineEdit_liquid_data(self) -> QLineEdit:
        return self.ui.lineEdit_liquid_data

    def get_lineEdit_oil(self) -> QLineEdit:
        return self.ui.lineEdit_oil

    def get_lineEdit_fluctuation_range(self) -> QLineEdit:
        return self.ui.lineEdit_fluctuation_range

    def get_lineEdit_stop_time(self) -> QLineEdit:
        return self.ui.lineEdit_stop_time

    def get_lineEdit_theory_diff(self) -> QLineEdit:
        return self.ui.lineEdit_theory_diff

    def get_lineEdit_theory_displacement(self) -> QLineEdit:
        return self.ui.lineEdit_theory_displacement

    def get_lineEdit_k_value(self) -> QLineEdit:
        return self.ui.lineEdit_k_value

    def get_lineEdit_daily_liquid(self) -> QLineEdit:
        return self.ui.lineEdit_daily_liquid

    def get_lineEdit_daily_oil(self) -> QLineEdit:
        return self.ui.lineEdit_daily_oil

    def get_lineEdit_time(self) -> QLineEdit:
        return self.ui.lineEdit_time

    def get_lineEdit_produce_oil(self) -> QLineEdit:
        return self.ui.lineEdit_produce_oil

    # ---------------------- 按钮控件getter ----------------------
    def get_calculate_button(self) -> QPushButton:
        return self.ui.pushButton_calculate

    def get_input_submit_button(self) -> QPushButton:
        return self.ui.pushButton_3  # 输入页提交

    def get_result_submit_button(self) -> QPushButton:
        return self.ui.pushButton_group1_submit  # 结果页提交


if __name__ == "__main__":
    app = QApplication([])
    w = OilStorageView()
    w.show()
    app.exec_()