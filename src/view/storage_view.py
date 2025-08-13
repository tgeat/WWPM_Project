from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit

# ✅ 假设 Ui_Form 是通过 Qt Designer 生成的 .ui 文件转化成的
from ..interface.storage_view_ui import Ui_Form

class StorageView(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.resize(1300,800)

    def get_lineEdit_wellNum(self) -> QLineEdit:
        return self.ui.lineEdit_wellNum

    def get_lineEdit_injectFuc(self) -> QLineEdit:
        return self.ui.lineEdit_injectFuc

    def get_lineEdit_reportTime(self) -> QLineEdit:
        return self.ui.lineEdit_reportTime

    def get_lineEdit_productLong(self) -> QLineEdit:
        return self.ui.lineEdit_productLong

    def get_lineEdit_mainLinePres(self) -> QLineEdit:
        return self.ui.lineEdit_mainLinePres

    def get_lineEdit_oilPres(self) -> QLineEdit:
        return self.ui.lineEdit_oilPres

    def get_lineEdit_casePres(self) -> QLineEdit:
        return self.ui.lineEdit_casePres

    def get_lineEdit_wellOilPres(self) -> QLineEdit:
        return self.ui.lineEdit_wellOilPres

    def get_lineEdit_daliyWater(self) -> QLineEdit:
        return self.ui.lineEdit_daliyWater

    def get_lineEdit_firstExecl(self) -> QLineEdit:
        return self.ui.lineEdit_firstExecl

    def get_lineEdit_firstWater(self) -> QLineEdit:
        return self.ui.lineEdit_firstWater

    def get_lineEdit_secondExecl(self) -> QLineEdit:
        return self.ui.lineEdit_secondExecl

    def get_lineEdit_secondWater(self) -> QLineEdit:
        return self.ui.lineEdit_secondWater

    def get_lineEdit_thirdExcel(self) -> QLineEdit:
        return self.ui.lineEdit_thirdExcel

    def get_lineEdit_thirdWater(self) -> QLineEdit:
        return self.ui.lineEdit_thirdWater

    def get_lineEdit_totalWater(self) -> QLineEdit:
        return self.ui.lineEdit_totalWater

    def get_lineEdit_note(self) -> QLineEdit:
        return self.ui.lineEdit_note


if __name__ == "__main__":
    app = QApplication([])
    w = StorageView()
    w.show()
    app.exec_()  # ✅ PyQt5 用 exec_()
