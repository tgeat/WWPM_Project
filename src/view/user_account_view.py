from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QApplication, QTableWidgetItem,
    QDialog, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from interface.user_account_ui import Ui_Form
from database.user_account_dao import (
    create_user, delete_user, get_user_by_username, list_users
)
from database.water_report_dao import list_children, list_root
from core.enums import AccountPermissionEnum
from typing import List
import sys

class HierarchySelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("请选择层级节点")
        self.resize(400, 500)

        # 主布局
        layout = QVBoxLayout(self)

        # 树控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout.addWidget(self.tree)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 构建树
        self.tree.blockSignals(True)
        try:
            self._build_tree()
        except Exception as e:
            print("构建树出错:", e)
        self.tree.blockSignals(False)

        self.tree.itemChanged.connect(self.on_item_changed)

    def _build_tree(self):
        for area in list_root():
            it_area = QTreeWidgetItem(self.tree, [area.area_name])
            it_area.setFlags(it_area.flags() & ~Qt.ItemIsUserCheckable)
            it_area.setData(0, Qt.UserRole, ("area", area.area_id))

            for team in list_children("area", area.area_id):
                it_team = QTreeWidgetItem(it_area, [team.team_name])
                it_team.setFlags(it_team.flags() | Qt.ItemIsUserCheckable)
                it_team.setCheckState(0, Qt.Unchecked)
                it_team.setData(0, Qt.UserRole, ("team", team.team_id))

                for room in list_children("team", team.team_id):
                    it_room = QTreeWidgetItem(it_team, [room.room_no])
                    it_room.setFlags(it_room.flags() & ~Qt.ItemIsUserCheckable)
                    it_room.setData(0, Qt.UserRole, ("room", room.id))

                    # 先列出所有 Bao（报）
                    baos = list_children("room", room.id)
                    for bao in baos:
                        if bao.bao_typeid == "水报":
                            it_water = QTreeWidgetItem(it_room, ["水报"])
                            it_water.setFlags(it_water.flags() | Qt.ItemIsUserCheckable)
                            it_water.setCheckState(0, Qt.Unchecked)
                            it_water.setData(0, Qt.UserRole, ("water", bao.id))

                            for well in list_children("bao", bao.id):
                                it_well = QTreeWidgetItem(it_water, [well.well_code])
                                it_well.setFlags(it_well.flags() & ~Qt.ItemIsUserCheckable)
                                it_well.setData(0, Qt.UserRole, ("well", well.id))

                        elif bao.bao_typeid == "油报":
                            it_oil = QTreeWidgetItem(it_room, ["油报"])
                            it_oil.setFlags(it_oil.flags() | Qt.ItemIsUserCheckable)
                            it_oil.setCheckState(0, Qt.Unchecked)
                            it_oil.setData(0, Qt.UserRole, ("oil", bao.id))

                            for platform in list_children("bao", bao.id):
                                it_platform = QTreeWidgetItem(it_oil, [platform.platformer_id])
                                it_platform.setFlags(it_platform.flags() & ~Qt.ItemIsUserCheckable)
                                it_platform.setData(0, Qt.UserRole, ("platform", platform.id))

                                for well in list_children("platform", platform.id):
                                    it_well = QTreeWidgetItem(it_platform, [well.well_code])
                                    it_well.setFlags(it_well.flags() & ~Qt.ItemIsUserCheckable)
                                    it_well.setData(0, Qt.UserRole, ("well", well.id))

        self.tree.expandAll()

    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        if item.checkState(0) != Qt.Checked:
            return

        parent = item.parent()
        if not parent:
            return

        role_type, _ = item.data(0, Qt.UserRole)

        # 限制：同一个注采班只能勾选一个
        if role_type == "team":
            grandparent = parent.parent()
            if grandparent:
                for i in range(grandparent.childCount()):
                    sibling_team = grandparent.child(i)
                    if sibling_team is not item and sibling_team.checkState(0) == Qt.Checked:
                        sibling_team.setCheckState(0, Qt.Unchecked)

        # 限制：计量间下“水报 / 油报”只能选一个
        if role_type in ("water", "oil"):
            for i in range(parent.childCount()):
                sibling = parent.child(i)
                sibling_type, _ = sibling.data(0, Qt.UserRole)
                if sibling is not item and sibling_type in ("water", "oil"):
                    if sibling.checkState(0) == Qt.Checked:
                        sibling.setCheckState(0, Qt.Unchecked)

    def get_selected_paths(self) -> List[str]:
        """
        遍历所有被勾选的项，返回路径列表，例如：
        ['作业区A_注采一班_计量间101_水报_井前60-11-13', …]
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
        permission_str = self.selections  # 应为 ['作业区_班'] 或 ['作业区_班_间_报类型']

        if not username or not password:
            QMessageBox.warning(self, "提示", "用户名和密码不能为空")
            return

        try:
            if not permission_str:
                raise ValueError("请选择用户权限")

            path = permission_str[0]
            parts = path.split("_")

            # 解析路径对应的权限类型
            if len(parts) == 2:
                # 高级权限：作业区_班
                permission = AccountPermissionEnum.Advanced.value + "_" + path
            elif len(parts) == 4:
                # 普通权限：作业区_班_间_报类型
                if "水报" in parts:
                    permission = AccountPermissionEnum.User1.value + "_" + path
                elif "油报" in parts:
                    permission = AccountPermissionEnum.User2.value + "_" + path
                else:
                    raise ValueError("无法识别的报类型，请检查")
            else:
                raise ValueError("不支持的路径结构")

            # 创建用户
            create_user(username, password, permission)
            QMessageBox.information(self, "成功", f"用户 {username} 添加成功")
            self.ui.LineEdit.clear()
            self.ui.LineEdit_2.clear()
            self.load_users()

        except ValueError as e:
            QMessageBox.warning(self, "添加用户失败", str(e))

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
        self.selections = []  # ✅ 初始化，防止未点击权限选择时报错

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
        if not self.selections:
            QMessageBox.warning(self, "提示", "请先选择用户权限")
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
