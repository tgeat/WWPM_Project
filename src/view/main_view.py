import sys

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QStackedWidget,
    QLabel, QHBoxLayout, QVBoxLayout
)

from .user_account_view import UserAccountPage, UserAccountPage_advanced
from .admin_view import AdminPage, AdvancedPage
from ..core.enums import AccountPermissionEnum

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("日报管理系统")
        self.resize(1300, 600)
        self._init_ui()


    def _init_ui(self):
        # —— 1. 导航栏 —— #
        self.nav_list = QListWidget()
        # 添加导航项
        self.nav_list.addItem("日报管理")
        self.nav_list.addItem("账号管理")
        # 固定导航栏宽度，使得不会随窗口大小变化
        self.nav_list.setFixedWidth(150)




        # —— 2. 页面容器 —— #
        self.stack = QStackedWidget()

        # 页面 1：简单的标签
        page_home = QWidget()
        v1 = QVBoxLayout(page_home)
        v1.addWidget(AdminPage())

        # 页面 2：设置页面
        page_settings = QWidget()
        v2 = QVBoxLayout(page_settings)
        v2.addWidget(UserAccountPage())




        # 把页面加入到 QStackedWidget
        self.stack.addWidget(page_home)      # index 0
        self.stack.addWidget(page_settings)  # index 1

        # —— 3. 信号：导航项切换时改变页面 —— #
        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        # 默认选中第一项
        self.nav_list.setCurrentRow(0)

        # —— 4. 布局 —— #
        h_layout = QHBoxLayout(self)
        h_layout.addWidget(self.nav_list)
        h_layout.addWidget(self.stack)
        h_layout.setStretch(0, 1)  # 导航栏占 1 份
        h_layout.setStretch(1, 4)  # 页面区域占 4 份

class MainWindow2(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("日报管理系统")
        self.resize(1300, 600)
        self.permission_list = []

    def put_account_info(self,permission):
        self.permission_list=permission.split("_")

    def init_ui(self):
        # —— 1. 导航栏 —— #
        self.nav_list = QListWidget()
        # 添加导航项
        self.nav_list.addItem("日报管理")
        self.nav_list.addItem("账号管理")
        # 固定导航栏宽度，使得不会随窗口大小变化
        self.nav_list.setFixedWidth(150)


        # —— 2. 页面容器 —— #
        self.stack = QStackedWidget()

        # 页面 1：简单的标签
        page_home = QWidget()
        v1 = QVBoxLayout(page_home)
        if self.permission_list[0] == AccountPermissionEnum.Advanced:
            advancedPage=AdvancedPage()
            advancedPage.put_account_info(self.permission_list)
            advancedPage.build_tree()
            v1.addWidget(advancedPage)
        else:
            v1.addWidget(AdminPage())

        # 页面 2：设置页面
        page_settings = QWidget()
        v2 = QVBoxLayout(page_settings)
        if self.permission_list[0] == AccountPermissionEnum.Advanced:
            userAccountPage_advanced=UserAccountPage_advanced()
            v2.addWidget(userAccountPage_advanced)
        else:
            v2.addWidget(UserAccountPage())


        # 把页面加入到 QStackedWidget
        self.stack.addWidget(page_home)      # index 0
        self.stack.addWidget(page_settings)  # index 1

        # —— 3. 信号：导航项切换时改变页面 —— #
        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        # 默认选中第一项
        self.nav_list.setCurrentRow(0)

        # —— 4. 布局 —— #
        h_layout = QHBoxLayout(self)
        h_layout.addWidget(self.nav_list)
        h_layout.addWidget(self.stack)
        h_layout.setStretch(0, 1)  # 导航栏占 1 份
        h_layout.setStretch(1, 4)  # 页面区域占 4 份

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
