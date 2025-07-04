from dataclasses import dataclass
from typing import Dict

@dataclass
class StorageModel:
    wellNum: str = ""
    injectFuc: str = ""
    reportTime: str = ""
    productLong: str = ""
    mainLinePres: str = ""
    oilPres: str = ""
    casePres: str = ""
    wellOilPres: str = ""
    daliyWater: str = ""
    firstExecl: str = ""
    firstWater: str = ""
    secondExecl: str = ""
    secondWater: str = ""
    thirdExcel: str = ""
    thirdWater: str = ""
    totalWater: str = ""
    note: str = ""

    # -------- 接口 1：从视图读取 --------
    @classmethod
    def from_view(cls, view) -> "StorageModel":
        """根据 StorageView 中的所有 lineEdit 填充数据模型"""
        return cls(
            wellNum=view.get_lineEdit_wellNum().text(),
            injectFuc=view.get_lineEdit_injectFuc().text(),
            productLong=view.get_lineEdit_productLong().text(),
            mainLinePres=view.get_lineEdit_mainLinePres().text(),
            oilPres=view.get_lineEdit_oilPres().text(),
            casePres=view.get_lineEdit_casePres().text(),
            wellOilPres=view.get_lineEdit_wellOilPres().text(),
            daliyWater=view.get_lineEdit_daliyWater().text(),
            firstExecl=view.get_lineEdit_firstExecl().text(),
            firstWater=view.get_lineEdit_firstWater().text(),
            secondExecl=view.get_lineEdit_secondExecl().text(),
            secondWater=view.get_lineEdit_secondWater().text(),
            thirdExcel=view.get_lineEdit_thirdExcel().text(),
            thirdWater=view.get_lineEdit_thirdWater().text(),
            totalWater=view.get_lineEdit_totalWater().text(),
            note=view.get_lineEdit_note().text()
        )

    # -------- 接口 2：写回到视图 --------
    def to_view(self, view) -> None:
        view.get_lineEdit_wellNum().setText(str(self.wellNum))
        view.get_lineEdit_injectFuc().setText(str(self.injectFuc))
        view.get_lineEdit_productLong().setText(str(self.productLong))
        view.get_lineEdit_mainLinePres().setText(str(self.mainLinePres))
        view.get_lineEdit_oilPres().setText(str(self.oilPres))
        view.get_lineEdit_casePres().setText(str(self.casePres))
        view.get_lineEdit_wellOilPres().setText(str(self.wellOilPres))
        view.get_lineEdit_daliyWater().setText(str(self.daliyWater))
        view.get_lineEdit_firstExecl().setText(str(self.firstExecl))
        view.get_lineEdit_secondExecl().setText(str(self.secondExecl))
        view.get_lineEdit_thirdExcel().setText(str(self.thirdExcel))
        view.get_lineEdit_totalWater().setText(str(self.totalWater))
        view.get_lineEdit_note().setText(str(self.note))

    # -------- 可选：转字典便于序列化 --------
    def to_dict(self) -> Dict[str, str]:
        return self.__dict__.copy()