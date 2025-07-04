# water_report_dao.py

from typing import Union, Sequence, Optional
from datetime import date
from typing import Optional, List, Dict
from sqlalchemy.exc import IntegrityError

from src.dataBase.db_schema import (
    SessionLocal, WorkArea, ProdTeam, MeterRoom, Well, DailyReport
)

from typing import List, Tuple, Union
from sqlalchemy.orm import Session

HierarchyObj = Union[WorkArea, ProdTeam, MeterRoom, Well]

# ---------- 基础：上下文管理 ----------
class DBSession:
    """with DBSession() as db: ..."""
    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            self.db.commit()
        self.db.close()

# ---------- 0. 顶层：列出所有作业区 ----------
def list_root() -> List[WorkArea]:
    """返回全部作业区"""
    with DBSession() as db:
        return db.query(WorkArea).order_by(WorkArea.area_name).all()

# ---------- 1. 作业区接口 ----------
def upsert_work_area(area_name: str) -> int:
    with DBSession() as db:
        obj = db.query(WorkArea).filter_by(area_name=area_name).first()
        if not obj:
            obj = WorkArea(area_name=area_name)
            db.add(obj)
            db.flush()          # 获取自增 id
        return obj.area_id


# ---------- 2. 注采班接口 ----------
def upsert_prod_team(area_id: int, team_no: int, team_name: str) -> int:
    with DBSession() as db:
        obj = (db.query(ProdTeam)
                 .filter_by(area_id=area_id, team_no=team_no)
                 .first())
        if not obj:
            obj = ProdTeam(area_id=area_id, team_no=team_no, team_name=team_name)
            db.add(obj)
            db.flush()
        else:
            obj.team_name = team_name  # 名称可能变
        return obj.team_id


# ---------- 3. 计量间接口 ----------
def upsert_meter_room(team_id: int, room_no: str, is_injection: bool = False) -> int:
    with DBSession() as db:
        obj = (db.query(MeterRoom)
                 .filter_by(team_id=team_id, room_no=room_no)
                 .first())
        if not obj:
            obj = MeterRoom(team_id=team_id,
                            room_no=room_no,
                            is_injection_room=int(is_injection))
            db.add(obj)
            db.flush()
        else:
            obj.is_injection_room = int(is_injection)
        return obj.room_id


# ---------- 4. 井接口 ----------
def upsert_well(room_id: int, well_code: str) -> int:
    with DBSession() as db:
        obj = (db.query(Well)
                 .filter_by(room_id=room_id, well_code=well_code)
                 .first())
        if not obj:
            obj = Well(room_id=room_id, well_code=well_code)
            db.add(obj)
            db.flush()
        return obj.well_id


# ---------- 5. 日报接口 ----------
def upsert_daily_report(well_id: int, rpt_dict: Dict) -> int:
    """
    rpt_dict 至少包含:
      • report_date (datetime.date)  • 其余列可选
    """
    with DBSession() as db:
        obj = (db.query(DailyReport)
                 .filter_by(well_id=well_id, report_date=rpt_dict["report_date"])
                 .first())
        if not obj:
            obj = DailyReport(well_id=well_id, **rpt_dict)
            db.add(obj)
        else:
            for k, v in rpt_dict.items():
                if k not in ("report_id", "well_id"):
                    setattr(obj, k, v)
        db.flush()
        return obj.report_id

def _recursive_delete(obj, db):
    """深度优先删除：先删所有子级，再删自己"""
    if isinstance(obj, WorkArea):
        for team in list(obj.teams):
            _recursive_delete(team, db)

    elif isinstance(obj, ProdTeam):
        for room in list(obj.rooms):
            _recursive_delete(room, db)

    elif isinstance(obj, MeterRoom):
        for well in list(obj.wells):
            _recursive_delete(well, db)

    elif isinstance(obj, Well):
        # 直接批量删日报提高效率
        db.query(DailyReport).filter_by(well_id=obj.well_id).delete(synchronize_session=False)

    # 最后删自身
    db.delete(obj)

def delete_entity(entity_type: str, entity_id: int) -> bool:
    """
    entity_type ∈ {'area', 'team', 'room', 'well', 'report'}
    """
    with DBSession() as db:
        mapper = {
            'area':  (WorkArea,  'area_id'),
            'team':  (ProdTeam,  'team_id'),
            'room':  (MeterRoom, 'room_id'),
            'well':  (Well,      'well_id'),
            'report':(DailyReport,'report_id')
        }
        if entity_type not in mapper:
            raise ValueError("未知实体类型")

        model_cls, pk = mapper[entity_type]
        obj = db.get(model_cls, entity_id)
        if not obj:
            return False

        if entity_type == 'report':
            db.delete(obj)              # 报表本身没子级
        else:
            _recursive_delete(obj, db)   # 递归级联
    return True

def _resolve_root(db: Session,
                  level: str,
                  key: Union[int, str]) -> HierarchyObj:
    """
    根据 level 和 key 找到当前节点对象
    level ∈ {"area","team","room","well"}
    key   可传 id(int) 也可传 name/code(str)
    """
    mapper = {
        "area":  WorkArea,
        "team":  ProdTeam,
        "room":  MeterRoom,
        "well":  Well
    }
    if level not in mapper:
        raise ValueError("level 必须是 area/team/room/well")

    model = mapper[level]
    if isinstance(key, int):
        return db.get(model, key)
    # name or code 查询
    filters = {
        WorkArea:  WorkArea.area_name == key,
        ProdTeam:  ProdTeam.team_name == key,
        MeterRoom: MeterRoom.room_no  == key,
        Well:      Well.well_code    == key
    }
    return db.query(model).filter(filters[model]).first()


def list_children(level: str,
                  key: Union[int, str]) -> List[HierarchyObj]:
    """
    根据当前节点（作业区 / 班组 / 间 / 井）获取其下一层级全部记录
    -------------------------------------------------------------
    level='area' key=3           -> 返回该作业区下所有 ProdTeam
    level='team' key='注采八班'   -> 返回该班组下所有 MeterRoom
    level='room' key=101         -> 返回该计量间下所有 Well
    level='well' key='前60-11-13'-> 返回该井下所有 DailyReport
    """
    with DBSession() as db:
        root = _resolve_root(db, level, key)
        if not root:
            return []

        if isinstance(root, WorkArea):
            return list(root.teams)  # type: List[ProdTeam]

        if isinstance(root, ProdTeam):
            return list(root.rooms)  # type: List[MeterRoom]

        if isinstance(root, MeterRoom):
            return list(root.wells)  # type: List[Well]

        if isinstance(root, Well):
            return list(root.reports)  # type: List[DailyReport]

        return []

def find_by_sequence(seq: Sequence[Union[int, str, date]]) -> Optional[Union[WorkArea, ProdTeam, MeterRoom, Well, DailyReport]]:
    """
    通过一个序列查找对应的层级对象或日报记录：
      • seq[0] 必须是 area 的 key（id:int 或 name:str）
      • seq[1] （可选）team 的 key（id:int 或 name:str）
      • seq[2] （可选）room 的 key（id:int 或 room_no:str）
      • seq[3] （可选）well 的 key（id:int 或 well_code:str）
      • seq[4] （可选）report_date（datetime.date）
    返回对应的 SQLAlchemy ORM 对象，找不到时返回 None。
    """
    # 映射层级与属性名
    child_attrs = {
        "team": ("teams", ProdTeam, "team_id", "team_name"),  # area -> teams
        "room": ("rooms", MeterRoom, "room_id", "room_no"),  # team -> rooms
        "well": ("wells", Well, "well_id", "well_code"),  # room -> wells
    }
    length = len(seq)
    if length < 1 or length > 5:
        raise ValueError("序列长度必须在 1 到 5 之间")
    # 1. 先 resolve area
    with DBSession() as db:
        area_key = seq[0]
        area = _resolve_root(db, "area", area_key)
        if not area:
            return None
        obj = area
        # 2. 依次遍历 team/room/well
        levels = ["team", "room", "well"]
        for idx, level in enumerate(levels, start=1):
            if length <= idx:
                break
            key = seq[idx]
            attr, model_cls, pk_attr, code_attr = child_attrs[level]
            children = getattr(obj, attr)
            match = None
            for child in children:
                # 按 id 或 名称/code 匹配
                if isinstance(key, int) and getattr(child, pk_attr) == key:
                    match = child
                    break
                if isinstance(key, str) and getattr(child, code_attr) == key:
                    match = child
                    break
            if not match:
                return None
            obj = match
        # 3. 如果有第五项，则查日报
        if length == 5:
            rpt_date = seq[4]
            if not isinstance(obj, Well):
                return None
            report = (
                db.query(DailyReport)
                  .filter_by(well_id=obj.well_id, report_date=rpt_date)
                  .first()
            )
            return report
        return obj

# ---------- ⬇️ 示例：把 StorageModel 写库 ----------
if __name__ == "__main__":
    # 1. 逐级确保外键存在
    area_id = upsert_work_area("作业二区")
    team_id = upsert_prod_team(area_id, team_no=8, team_name="注采七班")
    room_id = upsert_meter_room(team_id, room_no="104号", is_injection=False)
    well_id = upsert_well(room_id, well_code="前60-11-13")

    # 2. 准备日报字典（可来自 StorageModel.to_dict() 再字段映射）
    rpt = dict(
        report_date=date.today(),
        injection_mode="稳注",
        prod_hours=22,
        trunk_pressure=3.8,
        oil_pressure=3.5,
        casing_pressure=0.6,
        wellhead_pressure=3.3,
        plan_inject=120.0,
        actual_inject=119.7,
        remark="自动入库示例2",
        meter_stage1=40.1,
        meter_stage2=39.8,
        meter_stage3=39.8
    )

    report_id = upsert_daily_report(well_id, rpt)
    print(f"日报已写入，report_id={report_id}")
    #delete_entity("area",2)
    #print(f"作业区1已删除")

    # ① 通过 area_id 取其所有班组
    teams = list_children("area", "作业二区")
    print("班组列表：", [t.team_name for t in teams])

    # ② 通过班组名称取所有计量间
    rooms = list_children("team", "注采八班")
    print("计量间号：", [r.room_no for r in rooms])

    # ③ 通过 room_id 取所有井
    wells = list_children("room", 4)
    print("井号：", [w.well_code for w in wells])

    # ④ 通过井号取其全部日报
    reports = list_children("well", "前60-11-13")
    print("日报数：", len(reports))
