from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QApplication, QTableWidgetItem,
    QDialog, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from src.interface.user_account_ui import Ui_Form
from src.dataBase.user_account_dao import (
    create_user, delete_user, get_user_by_username, list_users
)
from src.dataBase.water_report_dao import   list_children,list_root,List
from src.core.enums import AccountPermissionEnum
import sys

class HierarchySelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("请选择层级节点")
        self.resize(400, 500)

        # 整体布局
        layout = QVBoxLayout(self)

        # 树控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout.addWidget(self.tree)

        # 确认/取消 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 构造树
        self._build_tree()

    def _build_tree(self):
        # 顶层“作业区”
        for area in list_root():
            it_area = QTreeWidgetItem(self.tree, [area.area_name])
            #it_area.setFlags(it_area.flags() | Qt.ItemIsUserCheckable)
            #it_area.setCheckState(0, Qt.Unchecked)
            it_area.setData(0, Qt.UserRole, ("area", area.area_id))

            # “注采班”
            for team in list_children("area", area.area_id):
                it_team = QTreeWidgetItem(it_area, [team.team_name])
                it_team.setFlags(it_team.flags() | Qt.ItemIsUserCheckable)
                it_team.setCheckState(0, Qt.Unchecked)
                it_team.setData(0, Qt.UserRole, ("team", team.team_id))

                # “计量间”
                for room in list_children("team", team.team_id):
                    it_room = QTreeWidgetItem(it_team, [room.room_no])
                    it_room.setFlags(it_room.flags() | Qt.ItemIsUserCheckable)
                    it_room.setCheckState(0, Qt.Unchecked)
                    it_room.setData(0, Qt.UserRole, ("room", room.room_id))

                    # “井”
                    for well in list_children("room", room.room_id):
                        it_well = QTreeWidgetItem(it_room, [well.well_code])
                        #it_well.setFlags(it_well.flags() | Qt.ItemIsUserCheckable)
                        #it_well.setCheckState(0, Qt.Unchecked)
                        it_well.setData(0, Qt.UserRole, ("well", well.well_id))

        self.tree.expandAll()

    def get_selected_paths(self) -> List[str]:
        """
        遍历所有被勾选的项，返回类似
        ['作业区A > 注采一班 > 计量间101 > 井前60-11-13', …]
        """
        paths = []

        def recurse(item: QTreeWidgetItem, prefix: List[str]):
            for i in range(item.childCount()):
                child = item.child(i)
                name = child.text(0)
                new_prefix = prefix + [name]

                if child.checkState(0) == Qt.Checked:
                    paths.append("_".join(new_prefix))

                recurse(child, new_prefix)

        root = self.tree.invisibleRootItem()
        recurse(root, [])
        return paths

class HierarchySelectDialog_advanced(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("请选择层级节点")
        self.resize(400, 500)

        # 整体布局
        layout = QVBoxLayout(self)

        # 树控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout.addWidget(self.tree)

        # 确认/取消 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 构造树
        self._build_tree()

    def _build_tree(self):
        # 顶层“作业区”
        for area in list_root():
            it_area = QTreeWidgetItem(self.tree, [area.area_name])
            #it_area.setFlags(it_area.flags() | Qt.ItemIsUserCheckable)
            #it_area.setCheckState(0, Qt.Unchecked)
            it_area.setData(0, Qt.UserRole, ("area", area.area_id))

            # “注采班”
            for team in list_children("area", area.area_id):
                it_team = QTreeWidgetItem(it_area, [team.team_name])
                #it_team.setFlags(it_team.flags() | Qt.ItemIsUserCheckable)
                #it_team.setCheckState(0, Qt.Unchecked)
                it_team.setData(0, Qt.UserRole, ("team", team.team_id))

                # “计量间”
                for room in list_children("team", team.team_id):
                    it_room = QTreeWidgetItem(it_team, [room.room_no])
                    it_room.setFlags(it_room.flags() | Qt.ItemIsUserCheckable)
                    it_room.setCheckState(0, Qt.Unchecked)
                    it_room.setData(0, Qt.UserRole, ("room", room.room_id))

                    # “井”
                    for well in list_children("room", room.room_id):
                        it_well = QTreeWidgetItem(it_room, [well.well_code])
                        #it_well.setFlags(it_well.flags() | Qt.ItemIsUserCheckable)
                        #it_well.setCheckState(0, Qt.Unchecked)
                        it_well.setData(0, Qt.UserRole, ("well", well.well_id))

        self.tree.expandAll()

    def get_selected_paths(self) -> List[str]:
        """
        遍历所有被勾选的项，返回类似
        ['作业区A > 注采一班 > 计量间101 > 井前60-11-13', …]
        """
        paths = []

        def recurse(item: QTreeWidgetItem, prefix: List[str]):
            for i in range(item.childCount()):
                child = item.child(i)
                name = child.text(0)
                new_prefix = prefix + [name]

                if child.checkState(0) == Qt.Checked:
                    paths.append("_".join(new_prefix))

                recurse(child, new_prefix)

        root = self.tree.invisibleRootItem()
        recurse(root, [])
        return paths

class UserAccountPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.resize(800, 500)

        # 设置 horizontalLayout 的伸缩比例为 5:1
        self.ui.horizontalLayout.setStretch(0, 5)  # 左侧 table
        self.ui.horizontalLayout.setStretch(1, 1)  # 右侧表单控件


        # 设置按钮文字
        self.ui.ComboBox.setText("请选择用户权限")
        # 点击弹出选择树对话框
        self.ui.ComboBox.clicked.connect(self._on_select_permissions)



        # 加载用户列表
        self.load_users()

        # 绑定按钮事件
        self.ui.PushButton.clicked.connect(self.add_user)
        self.ui.PushButton_2.clicked.connect(self.delete_user)

    def _on_select_permissions(self):
        dlg = HierarchySelectDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            # 获取用户勾选的完整路径列表
            self.selections = dlg.get_selected_paths()
            # 比如把第一个路径显示回按钮上
            if self.selections:
                self.ui.ComboBox.setText(self.selections[0])

    def load_users(self):
        self.ui.TableWidget.setRowCount(0)
        users = list_users()
        for user in users:
            row = self.ui.TableWidget.rowCount()
            self.ui.TableWidget.insertRow(row)
            self.ui.TableWidget.setItem(row, 0, self._create_item(user.username))
            self.ui.TableWidget.setItem(row, 1, self._create_item(user.permission))

    def add_user(self):
        username = self.ui.LineEdit.text().strip()
        password = self.ui.LineEdit_2.text().strip()
        permission_str = self.selections

        if not username or not password:
            QMessageBox.warning(self, "提示", "用户名和密码不能为空")
            return


        try:
            if len(permission_str[0].split("_"))==2:
                permission = AccountPermissionEnum.Advanced+"_"+permission_str[0]
            elif len(permission_str[0].split("_"))==3:
                permission = AccountPermissionEnum.User+"_"+permission_str[0]
            create_user(username, password, permission)
            QMessageBox.information(self, "成功", f"用户 {username} 添加成功")
            self.ui.LineEdit.clear()
            self.ui.LineEdit_2.clear()
            self.load_users()
        except ValueError as e:
            QMessageBox.warning(self, "失败", str(e))

    def delete_user(self):
        selected = self.ui.TableWidget.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "提示", "请先选择一个用户")
            return

        username = self.ui.TableWidget.item(selected, 0).text()
        user = get_user_by_username(username)
        if user:
            if delete_user(user.user_id):
                QMessageBox.information(self, "成功", f"用户 {username} 已删除")
                self.load_users()
            else:
                QMessageBox.warning(self, "失败", "删除失败")
        else:
            QMessageBox.warning(self, "失败", "用户不存在")

    def _create_item(self, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

class UserAccountPage_advanced(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.resize(800, 500)

        # 设置 horizontalLayout 的伸缩比例为 5:1
        self.ui.horizontalLayout.setStretch(0, 5)  # 左侧 table
        self.ui.horizontalLayout.setStretch(1, 1)  # 右侧表单控件


        # 设置按钮文字
        self.ui.ComboBox.setText("请选择用户权限")
        # 点击弹出选择树对话框
        self.ui.ComboBox.clicked.connect(self._on_select_permissions)



        # 加载用户列表
        self.load_users()

        # 绑定按钮事件
        self.ui.PushButton.clicked.connect(self.add_user)
        self.ui.PushButton_2.clicked.connect(self.delete_user)

    def _on_select_permissions(self):
        dlg = HierarchySelectDialog_advanced(self)
        if dlg.exec_() == QDialog.Accepted:
            # 获取用户勾选的完整路径列表
            self.selections = dlg.get_selected_paths()
            # 比如把第一个路径显示回按钮上
            if self.selections:
                self.ui.ComboBox.setText(self.selections[0])

    def load_users(self):
        self.ui.TableWidget.setRowCount(0)
        users = list_users()
        for user in users:
            row = self.ui.TableWidget.rowCount()
            self.ui.TableWidget.insertRow(row)
            self.ui.TableWidget.setItem(row, 0, self._create_item(user.username))
            self.ui.TableWidget.setItem(row, 1, self._create_item(user.permission))

    def add_user(self):
        username = self.ui.LineEdit.text().strip()
        password = self.ui.LineEdit_2.text().strip()
        permission_str = self.selections

        if not username or not password:
            QMessageBox.warning(self, "提示", "用户名和密码不能为空")
            return


        try:
            if len(permission_str[0].split("_"))==2:
                permission = AccountPermissionEnum.Advanced+"_"+permission_str[0]
            elif len(permission_str[0].split("_"))==3:
                permission = AccountPermissionEnum.User+"_"+permission_str[0]
            create_user(username, password, permission)
            QMessageBox.information(self, "成功", f"用户 {username} 添加成功")
            self.ui.LineEdit.clear()
            self.ui.LineEdit_2.clear()
            self.load_users()
        except ValueError as e:
            QMessageBox.warning(self, "失败", str(e))

    def delete_user(self):
        selected = self.ui.TableWidget.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "提示", "请先选择一个用户")
            return

        username = self.ui.TableWidget.item(selected, 0).text()
        user = get_user_by_username(username)
        if user:
            if delete_user(user.user_id):
                QMessageBox.information(self, "成功", f"用户 {username} 已删除")
                self.load_users()
            else:
                QMessageBox.warning(self, "失败", "删除失败")
        else:
            QMessageBox.warning(self, "失败", "用户不存在")

    def _create_item(self, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserAccountPage()
    window.show()
    sys.exit(app.exec_())
