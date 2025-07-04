
from PyQt5.QtWidgets import QApplication

from src.core.enums import AccountPermissionEnum
from src.controller.login_controller import LoginPresenter
from src.main_page import MainWindow,MainWindow2
from src.controller.storage_controller import StorageController

def main():
    app = QApplication([])

    app.setQuitOnLastWindowClosed(True)

    # 1) 创建登录 Presenter 和它对应的 View
    login_presenter = LoginPresenter()
    storage_controller = StorageController()
    login_view = login_presenter.get_view()
    storage_view = storage_controller.get_view()
    main_window = MainWindow()
    main_window2=MainWindow2()




    # 2) 登录完成后的回调
    def start(permission):
        # permission 已经是 AccountPermissionEnum 枚举对象
        if permission.split("_")[0] == AccountPermissionEnum.Admin:
            # 创建并显示主窗口
            main_window.show()
        elif permission.split("_")[0] == AccountPermissionEnum.Advanced:
            # 创建并显示主窗口
            main_window2.put_account_info(permission)
            main_window2.init_ui()
            main_window2.show()
        elif permission.split("_")[0] == AccountPermissionEnum.User:
            # 创建并显示主窗口
            storage_controller.put_accout_info(permission)
            storage_controller.creat_model_list()
            storage_controller.creat_table()
            storage_view.showMaximized()
        else:
            return

    # 3) 连接信号
    # 假设 LoginPresenter 里定义为: user_permission_signal = Signal(object)
    login_presenter.user_permission_signal.connect(start)

    # 4) 显示登录界面，进入事件循环
    login_view.show()
    app.exec_()

if __name__ == "__main__":
    main()
