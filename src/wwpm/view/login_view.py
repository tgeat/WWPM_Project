from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QMessageBox
)

class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def get_username_lineEdit(self) -> QLineEdit:
        return self._username_lineEdit

    def get_password_lineEdit(self) -> QLineEdit:
        return self._password_lineEdit

    def get_login_button(self) -> QPushButton:
        return self._login_button

    def show_login_failed(self):
        QMessageBox.warning(self, "登录失败", "用户名或密码错误")
        self.clear()

    def clear(self):
        self._username_lineEdit.clear()
        self._password_lineEdit.clear()

    def _init_ui(self):
        self.setWindowTitle("登录")
        self.resize(350, 300)

        # 标题
        self._title_label = QLabel("登录")
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 用户名
        self._username_label = QLabel("账号")
        self._username_lineEdit = QLineEdit()
        self._username_lineEdit.setPlaceholderText("请输入用户名")

        # 密码
        self._password_label = QLabel("密码")
        self._password_lineEdit = QLineEdit()
        self._password_lineEdit.setEchoMode(QLineEdit.Password)
        self._password_lineEdit.setPlaceholderText("请输入密码")

        # 登录按钮
        self._login_button = QPushButton("登录")

        # 布局
        user_name_layout = QHBoxLayout()
        user_name_layout.addWidget(self._username_label)
        user_name_layout.addWidget(self._username_lineEdit)

        password_layout = QHBoxLayout()
        password_layout.addWidget(self._password_label)
        password_layout.addWidget(self._password_lineEdit)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self._title_label)
        main_layout.addLayout(user_name_layout)
        main_layout.addLayout(password_layout)
        main_layout.addWidget(self._login_button)

        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication([])
    view = LoginView()
    view.show()
    app.exec_()  # 注意：PyQt5 用 exec_()
