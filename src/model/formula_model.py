from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class Formula:
    """简单的公式数据模型，包含左侧和右侧表达式"""
    left: str
    right: str

    @classmethod
    def from_row(cls, row: Iterable[str]) -> "Formula":
        left = str(row[0]).strip()
        right = "".join(str(cell).strip() for cell in row[2:] if str(cell).strip())
        return cls(left=left, right=right)

    def is_valid(self) -> bool:
        return bool(self.left) and bool(self.right)


def from_table_data(table_data: Iterable[Iterable[str]]) -> List[Formula]:
    """将视图中的二维表格数据转换为公式对象列表"""
    formulas: List[Formula] = []
    for row in table_data:
        formula = Formula.from_row(row)
        if formula.is_valid():
            formulas.append(formula)
    return formulas
