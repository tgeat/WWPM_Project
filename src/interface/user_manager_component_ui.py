# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(617, 488)
        Form.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout_2.addItem(spacerItem)

        self.TitleLabel = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.TitleLabel.sizePolicy().hasHeightForWidth())
        self.TitleLabel.setSizePolicy(sizePolicy)
        self.TitleLabel.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        self.TitleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.TitleLabel.setObjectName("TitleLabel")
        self.horizontalLayout_2.addWidget(self.TitleLabel)

        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.TableWidget = QtWidgets.QTableWidget(Form)
        self.TableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.TableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.TableWidget.setShowGrid(False)
        self.TableWidget.setObjectName("TableWidget")
        self.TableWidget.setColumnCount(2)
        self.TableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.TableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.TableWidget.setHorizontalHeaderItem(1, item)
        self.TableWidget.horizontalHeader().setStretchLastSection(True)
        self.TableWidget.verticalHeader().setSortIndicatorShown(False)
        self.horizontalLayout.addWidget(self.TableWidget)

        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        self.LineEdit = QtWidgets.QLineEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.LineEdit.sizePolicy().hasHeightForWidth())
        self.LineEdit.setSizePolicy(sizePolicy)
        self.LineEdit.setObjectName("LineEdit")
        self.verticalLayout.addWidget(self.LineEdit)

        self.LineEdit_2 = QtWidgets.QLineEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.LineEdit_2.sizePolicy().hasHeightForWidth())
        self.LineEdit_2.setSizePolicy(sizePolicy)
        self.LineEdit_2.setObjectName("LineEdit_2")
        self.verticalLayout.addWidget(self.LineEdit_2)

        self.ComboBox = QtWidgets.QPushButton(Form)  # 实为按钮伪装下拉行为
        self.ComboBox.setObjectName("ComboBox")
        self.verticalLayout.addWidget(self.ComboBox)

        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)

        self.PushButton = QtWidgets.QPushButton(Form)
        self.PushButton.setObjectName("PushButton")
        self.verticalLayout.addWidget(self.PushButton)

        self.PushButton_2 = QtWidgets.QPushButton(Form)
        self.PushButton_2.setObjectName("PushButton_2")
        self.verticalLayout.addWidget(self.PushButton_2)

        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.TitleLabel.setText(_translate("Form", "用户账号管理"))
        self.TableWidget.setSortingEnabled(True)
        item = self.TableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "用户名"))
        item = self.TableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "权限"))
        self.LineEdit.setPlaceholderText(_translate("Form", "用户名"))
        self.LineEdit_2.setPlaceholderText(_translate("Form", "密码"))
        self.ComboBox.setText(_translate("Form", "选择权限"))
        self.PushButton.setText(_translate("Form", "添加账户"))
        self.PushButton_2.setText(_translate("Form", "删除账户"))
