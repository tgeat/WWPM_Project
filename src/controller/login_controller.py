from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

import os
import sys

# Ensure the project root is available on ``sys.path`` so that absolute
# imports like ``from database`` work when this module is executed
# directly without installing the package.  This mirrors the behaviour of
# running the project as an installed distribution.
module_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(module_dir)
project_root = os.path.dirname(src_dir)
if project_root not in sys.path:  # pragma: no cover - runtime fix
    sys.path.insert(0, project_root)

from src.view.login_view import LoginView
from src.database import user_account_dao as user_dao
from src.core.enums import AccountPermissionEnum

class LoginPresenter(QObject):
    login_status_signal = pyqtSignal(bool)
    user_permission_signal = pyqtSignal(object)  # 不能直接使用 Enum 类型

    def __init__(self):
        super().__init__()
        self._login_view = LoginView()

        self._connect_signals()

    def get_view(self):
        return self._login_view

    def login(self, username, password):
        if not user_dao.check_password(username, password):
            self._login_view.show_login_failed()
            self.login_status_signal.emit(False)
            return False

        account = user_dao.get_user(username)

        # 为避免关闭延迟，先 hide 再 close
        self._login_view.hide()
        self._login_view.close()
        self.user_permission_signal.emit(account.permission)
        self.login_status_signal.emit(True)
        return True

    def _connect_signals(self):
        self.get_view().get_login_button().clicked.connect(
            lambda: self.login(
                self.get_view().get_username_lineEdit().text(),
                self.get_view().get_password_lineEdit().text(),
            )
        )

if __name__ == "__main__":
    app = QApplication([])
    login_presenter = LoginPresenter()
    login_presenter.get_view().show()
    app.exec_()
