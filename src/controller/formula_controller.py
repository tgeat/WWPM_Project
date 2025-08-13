import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

from database import formula_dao
from model import formula_model
from view.formula_view import FormulaImportDialog


class FormulaController:
    def __init__(self):
        self.view = FormulaImportDialog()
        self.view.get_import_button().clicked.connect(self.import_to_mysql)

    def import_to_mysql(self):
        table_data = self.view.get_table_data()
        formulas = formula_model.from_table_data(table_data)
        total = formula_dao.upsert_formulas(formulas)
        QMessageBox.information(self.view, "导出成功", f"导出完成：共处理 {total} 条公式")

    def show(self):
        self.view.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = FormulaController()
    controller.show()
    sys.exit(app.exec_())
