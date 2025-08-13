#信息提示对话框基类。用于具体的提示框继承和调用

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets import MessageBox
from qfluentwidgets.components import (
    InfoBar,
    InfoBarIcon,
    InfoBarPosition,
    PushButton,
    StateToolTip,
)

class MessageBaseView(QWidget):

    info_button_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setParent(parent)
        self.is_state_tooltip_running = False

    def show_mask_dialog(self, title: str = "Title", content: str = "Content") -> bool:
        """显示一个遮罩式的对话框

        Args:
            title (str): 标题
            content (str): 内容

        Returns:
            bool: 是否点击了确定按钮
        """
        w = MessageBox(title, content, self)
        return bool(w.exec())

if __name__ == "__main__":
    app = QApplication([])
    w = MessageBaseView()
    w.show()
    app.exec()