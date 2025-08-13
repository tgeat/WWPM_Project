# water_report_dao.py


from datetime import date
from typing import Optional, Dict, List, Union

from database.db_schema import Base

from database.db_schema import (
    SessionLocal, WorkArea, ProdTeam, MeterRoom, Well, DailyReport, Platformer, Bao, OilWellDatas
)
from sqlalchemy.orm import Session

HierarchyObj = Union[WorkArea, ProdTeam, MeterRoom, Bao, Platformer, Well, DailyReport]

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

# ---------- 1. 返回全部作业区 ----------
def list_root() -> List[WorkArea]:
    """返回全部作业区"""
    with DBSession() as db:
        return db.query(WorkArea).order_by(WorkArea.area_name).all()


# ---------- 2. 作业区接口 ----------
def upsert_work_area(area_name: str) -> int:
    with DBSession() as db:
        obj = db.query(WorkArea).filter_by(area_name=area_name).first()
        if not obj:
            obj = WorkArea(area_name=area_name)
            db.add(obj)
            db.flush()
        return obj.area_id


# ---------- 3. 注采班接口 ----------
def upsert_prod_team(area_id: int, team_no: int, team_name: str) -> int:
    with DBSession() as db:
        obj = db.query(ProdTeam).filter_by(area_id=area_id, team_no=team_no).first()
        if not obj:
            obj = ProdTeam(area_id=area_id, team_no=team_no, team_name=team_name)
            db.add(obj)
            db.flush()
        else:
            obj.team_name = team_name
        return obj.team_id


# ---------- 4. 计量间接口 ----------
def upsert_meter_room(team_id: int, room_no: str, is_injection: bool = False) -> int:
    with DBSession() as db:
        obj = db.query(MeterRoom).filter_by(team_id=team_id, room_no=room_no).first()
        if not obj:
            obj = MeterRoom(team_id=team_id,
                            room_no=room_no,
                            is_injection_room=int(is_injection))
            db.add(obj)
            db.flush()
        else:
            obj.is_injection_room = int(is_injection)
        return obj.id

# ---------- 5. 报接口（修正字段名） ----------
def upsert_bao(room_id: int, bao_type: str) -> int:
    """
    插入或获取计量间下的报类型（如“水报”或“油报”）
    """
    with DBSession() as db:
        obj = db.query(Bao).filter_by(room_id=room_id, bao_typeid=bao_type).first()
        if not obj:
            obj = Bao(room_id=room_id, bao_typeid=bao_type)
            db.add(obj)
            db.flush()
        return obj.id

# ---------- 5. 平台接口 ----------
def upsert_platformer(bao_id: int, platform_name: str) -> int:
    with DBSession() as db:
        obj = (db.query(Platformer)
                 .filter_by(bao_id=bao_id, platformer_id=platform_name)
                 .first())
        if not obj:
            obj = Platformer(bao_id=bao_id, platformer_id=platform_name)
            db.add(obj)
            db.flush()
        return obj.id

def create_default_oil_report(db, well_id: str, well_code: str, platform: str) -> OilWellDatas:
    """
    创建一个空日报数据对象（仅含well_id、井号、平台、日期，其他字段为空）
    """
    default_report = OilWellDatas(
        well_id=well_id,
        well_code=well_code,
        platform=platform,
        create_time=date.today(),

        oil_pressure="",
        casing_pressure="",
        back_pressure="",
        time_sign="",
        total_bucket_sign="",
        total_bucket="",
        press_data="",
        prod_hours="",
        a2_stroke="",
        a2_frequency="",
        work_stroke="",
        effective_stroke="",
        fill_coeff_test="",
        lab_water_cut="",
        reported_water="",
        fill_coeff_liquid="",
        last_tubing_time="",
        pump_diameter="",
        block="",
        transformer="",
        remark="",
        liquid_per_bucket="",
        sum_value="",
        liquid1="",
        production_coeff="",
        a2_24h_liquid="",
        liquid2="",
        oil_volume="",
        fluctuation_range="",
        shutdown_time="",
        theory_diff="",
        theory_displacement="",
        k_value="",
        daily_liquid="",
        daily_oil="",
        well_times="",
        production_time="",
        total_oil=""
    )
    db.add(default_report)

# ---------- 6. 油井接口 ----------
def upsert_well(well_code: str, bao_type: str,
                bao_id: Optional[int] = None,
                platform_id: Optional[int] = None) -> int:
    """
    创建新井（不再 upsert，而是 insert-only）
    - 水报井挂在 bao 下
    - 油报井挂在 platform 下
    - well_code 可重名
    """
    with DBSession() as db:
        if bao_type == "水报":
            if bao_id is None:
                raise ValueError("水报类型必须提供 bao_id")
            # 获取 room_id
            bao = db.get(Bao, bao_id)
            if not bao:
                raise ValueError("找不到指定的水报")
            room_id = bao.room_id

            # 直接创建新井（允许重名）
            obj = Well(room_id=room_id, bao_id=bao_id, platform_id=None, well_code=well_code)
            db.add(obj)
            db.flush()
            return obj.id

        elif bao_type == "油报":
            if platform_id is None:
                raise ValueError("油报类型必须提供 platform_id")
            platform = db.get(Platformer, platform_id)
            if not platform:
                raise ValueError("找不到指定的平台")
            bao_id = platform.bao_id
            room_id = platform.bao.room_id if platform.bao else None

            # 直接创建新井（允许重名）
            obj = Well(room_id=room_id, bao_id=bao_id, platform_id=platform_id, well_code=well_code)
            db.add(obj)
            db.flush()
            create_default_oil_report(db, obj.id, well_code, platform.platformer_id)
            return obj.id

        else:
            raise ValueError(f"未知报类型：{bao_type}")

# ---------- 7. 水井接口 ----------
def upsert_water_well(bao_id: int, well_code: str) -> int:
    """
    创建水井：
    - 根据 bao_id 找到对应 room_id
    - 查找是否已有该 room_id + well_code 的井，有则返回
    - 否则新建，保证 bao_id 非空
    """
    with DBSession() as db:
        bao = db.get(Bao, bao_id)
        if not bao:
            raise ValueError("找不到指定的水报")

        room_id = bao.room_id
        obj = db.query(Well).filter_by(room_id=room_id, well_code=well_code).first()

        if not obj:
            obj = Well(room_id=room_id, bao_id=bao_id, platform_id=None, well_code=well_code)
            db.add(obj)
            db.flush()
        return obj.id

# ---------- 8. 水报数据接口 ----------
def upsert_daily_report(well_id: int, rpt_dict: Dict) -> int:
    """
    插入或更新日报
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

# ---------- 9. 油报数据接口 ----------
def upsert_oil_report(well_id: int, rpt_dict: dict) -> int:
    """
    插入或更新油报日报
    """
    with DBSession() as db:
        obj = (db.query(OilWellDatas)
                 .filter_by(well_id=well_id, create_time=rpt_dict["create_time"])
                 .first())
        if not obj:
            obj = OilWellDatas(well_id=well_id, **rpt_dict)
            db.add(obj)
        else:
            for k, v in rpt_dict.items():
                # 排除主键和外键，不更新它们
                if k not in ("id", "well_id"):
                    setattr(obj, k, v)
        db.flush()
        return obj.id

def _recursive_delete(obj, db):
    """深度优先删除：先删所有子级，再删自己"""
    if isinstance(obj, WorkArea):
        for team in list(obj.teams):
            _recursive_delete(team, db)

    elif isinstance(obj, ProdTeam):
        for room in list(obj.rooms):
            _recursive_delete(room, db)

    elif isinstance(obj, MeterRoom):
        # 注意关系名改成单数bao
        for bao in list(obj.bao):
            _recursive_delete(bao, db)

    elif isinstance(obj, Bao):
        if obj.bao_typeid == "水报":
            for well in list(obj.wells):
                _recursive_delete(well, db)
        elif obj.bao_typeid == "油报":
            for platform in list(obj.platforms):
                _recursive_delete(platform, db)

    elif isinstance(obj, Platformer):
        for well in list(obj.wells):
            _recursive_delete(well, db)

    elif isinstance(obj, Well):
        # 删除水报
        db.query(DailyReport).filter_by(well_id=obj.id).delete(synchronize_session=False)
        # 删除油报
        db.query(OilWellDatas).filter_by(well_id=obj.id).delete(synchronize_session=False)
    db.delete(obj)

def delete_entity(entity_type: str, entity_id: int) -> bool:
    """
    entity_type ∈ {'area', 'team', 'room', 'bao', 'platform', 'well', 'report'}
    """
    with DBSession() as db:
        mapper = {
            'area': (WorkArea, 'area_id'),
            'team': (ProdTeam, 'team_id'),
            'room': (MeterRoom, 'id'),           # 修改这里
            'bao': (Bao, 'id'),
            'platform': (Platformer, 'id'),
            'well': (Well, 'id'),                # 修改这里
            'report': (DailyReport, 'report_id')
        }
        if entity_type not in mapper:
            raise ValueError("未知实体类型")

        model_cls, pk = mapper[entity_type]
        obj = db.get(model_cls, entity_id)
        if not obj:
            return False

        if entity_type == 'report':
            db.delete(obj)              # 报表无子级，直接删除
        else:
            _recursive_delete(obj, db)   # 递归级联删除
        db.commit()
    return True

def _resolve_root(db: Session,
                  level: str,
                  key: Union[int, str]) -> Optional[Base]:
    """
    根据 level 和 key 找到当前节点对象
    level ∈ {"area", "team", "room", "bao", "platform", "well", "report"}
    key   可传 id(int) 也可传 name/code(str)
    """
    mapper = {
        'area':     WorkArea,
        'team':     ProdTeam,
        'room':     MeterRoom,
        'bao':      Bao,
        'platform': Platformer,
        'well':     Well,
        'report':   DailyReport
    }

    if level not in mapper:
        raise ValueError("level 必须是 area/team/room/bao/platform/well/report")

    model = mapper[level]

    if isinstance(key, int):
        return db.get(model, key)

    filters = {
        WorkArea:   WorkArea.area_name == key,
        ProdTeam:   ProdTeam.team_name == key,
        MeterRoom:  MeterRoom.room_no == key,
        Bao:        Bao.bao_typeid == key,
        Platformer: Platformer.platformer_id == key,
        Well:       Well.well_code == key,
        # DailyReport 不支持字符串查找，保持无
    }

    if model not in filters:
        raise ValueError(f"{level} 暂不支持字符串方式查找")

    return db.query(model).filter(filters[model]).first()


from sqlalchemy.orm import joinedload

def list_children(level: str, key: Union[int, str]) -> List[Base]:
    """
    根据当前节点（作业区 / 班组 / 间 / 报 / 平台 / 井）获取其下一层级全部记录
    """
    with DBSession() as db:
        root = _resolve_root(db, level, key)
        if not root:
            return []

        if isinstance(root, WorkArea):
            return list(root.teams)

        if isinstance(root, ProdTeam):
            return list(root.rooms)


        if isinstance(root, MeterRoom):
            # 一次性加载两个报
            room_with_bao = db.query(MeterRoom).options(joinedload(MeterRoom.bao)).filter_by(id=root.id).one()
            bao_list = list(room_with_bao.bao)
            return bao_list

        if isinstance(root, Bao):
            if root.bao_typeid == "水报":
                bao_with_wells = db.query(Bao).options(joinedload(Bao.wells)).filter_by(id=root.id).one()
                return list(bao_with_wells.wells)
            elif root.bao_typeid == "油报":
                bao_with_platforms = db.query(Bao).options(
                    joinedload(Bao.platforms).joinedload(Platformer.wells)).filter_by(id=root.id).one()
                return list(bao_with_platforms.platforms)
            else:
                return []

        if isinstance(root, Platformer):
            # ✅ 加载 wells（若你单独 list_children("platform", id) 也要加）
            root = db.query(Platformer).options(joinedload(Platformer.wells)).get(root.id)
            return list(root.wells)

        if isinstance(root, Well):
            # 区分油井日报和水井日报
            if root.platform is not None:
                bao_typeid = getattr(root.platform.bao, "bao_typeid", "")
            else:
                bao_typeid = getattr(root.bao, "bao_typeid", "")

            if "油报" in bao_typeid:
                return list(root.oil_well_reports)
            else:
                return list(root.reports)

        return []

def find_by_sequence(seq: List[Union[int, str, date]]) -> Optional[HierarchyObj]:
    """
    通过一个序列查找层级对象或日报记录，支持新结构：
    area → team → room → bao → (well | platform → well) → report
    """
    if not (1 <= len(seq) <= 7):
        raise ValueError("序列长度必须在 1 到 7 之间")

    with DBSession() as db:
        # 1. 作业区
        area = _resolve_root(db, "area", seq[0])
        if not area:
            return None
        obj = area
        if len(seq) == 1:
            return obj

        # 2. 班组
        team = next((t for t in area.teams if seq[1] == t.team_id or seq[1] == t.team_name), None)
        if not team:
            return None
        obj = team
        if len(seq) == 2:
            return obj

        # 3. 计量间
        room = next((r for r in team.rooms if seq[2] == r.id or seq[2] == r.room_no), None)
        if not room:
            return None
        obj = room
        if len(seq) == 3:
            return obj

        # 4. 报（油报或水报）
        bao = next((b for b in room.bao if seq[3] == b.id or seq[3] == b.bao_typeid), None)
        if not bao:
            return None
        obj = bao
        if len(seq) == 4:
            return obj

        # 5. 如果是水报 → 井
        if bao.bao_typeid == "水报":
            well = next((w for w in bao.wells if seq[4] == w.id or seq[4] == w.well_code), None)
            if not well:
                return None
            obj = well
            if len(seq) == 5:
                return obj

            # 6. 报表
            if len(seq) > 5 and isinstance(seq[5], date):
                return db.query(DailyReport).filter_by(well_id=well.id, report_date=seq[5]).first()

        # 5. 如果是油报 → 平台
        elif bao.bao_typeid == "油报":
            platform = next((p for p in bao.platforms if seq[4] == p.id or seq[4] == p.platformer_id), None)
            if not platform:
                return None
            obj = platform
            if len(seq) == 5:
                return obj

            # 6. 平台 → 井
            well = next((w for w in platform.wells if seq[5] == w.id or seq[5] == w.well_code), None)
            if not well:
                return None
            obj = well
            if len(seq) == 6:
                return obj

            # 7. 报表
                # 7. 查油井日报（OilWellDatas）
            if len(seq) > 6 and isinstance(seq[6], date):
                return db.query(OilWellDatas).filter_by(well_code=well.well_code, create_time=seq[6]).first()
        return None

# ---------- ⬇️ 示例：把 StorageModel 写库 ----------
if __name__ == "__main__":
    from datetime import date

    # === 1. 逐级构建层级结构 ===
    area_id = upsert_work_area("作业区D")
    team_id = upsert_prod_team(area_id, team_no=10, team_name="注采十班")
    room_id = upsert_meter_room(team_id, room_no="106号", is_injection=False)

    # === 2. 在间下插入水报和油报 ===
    water_bao_id = upsert_bao(room_id, bao_type="水报")
    oil_bao_id = upsert_bao(room_id, bao_type="油报")

    # === 3. 在油报下插入平台 ===
    platform_id = upsert_platformer(oil_bao_id, platform_name="平台Beta")

    # === 4. 插入井：水井直接挂在水报下，油井挂在平台下 ===
    # 这里调用upsert_well需要传正确的参数，水报需要bao_id，油报需要platform_id
    water_well_id = upsert_well(well_code="水井-D1", bao_type="水报", bao_id=water_bao_id)
    oil_well_id = upsert_well(well_code="油井-D2", bao_type="油报", platform_id=platform_id)

    # === 5. 插入日报（给水井插入）===
    rpt = dict(
        report_date=date.today(),
        injection_mode="稳注",
        prod_hours=20,
        trunk_pressure=3.2,
        oil_pressure=3.1,
        casing_pressure=0.5,
        wellhead_pressure=3.0,
        plan_inject=110.0,
        actual_inject=109.8,
        remark="测试日报",
        meter_stage1=41.1,
        meter_stage2=40.9,
        meter_stage3=40.7
    )
    report_id = upsert_daily_report(water_well_id, rpt)
    print(f"日报已写入，report_id={report_id}")

    # === 5b. 插入油井日报（OilWellDatas）===
    oil_rpt = dict(
        create_time=date.today(),
        well_code="井号",
        platform="平台",
        oil_pressure="套压",
        casing_pressure="1.2",
        back_pressure="2.5",
        time_sign="08:00",
        total_bucket_sign="Y",
        total_bucket="图像A",
        press_data="10.2",
        prod_hours="24",
        a2_stroke="2.8",
        a2_frequency="5.6",
        work_stroke="22.5",
        effective_stroke="1500",
        fill_coeff_test="0.9",
        lab_water_cut="70%",
        reported_water="68%",
        fill_coeff_liquid="15.0",
        last_tubing_time="120",
        pump_diameter="32",
        block="一区",
        transformer="T-1",
        remark="测试插入",
        liquid_per_bucket="0.9",
        sum_value="100",
        liquid1="5.0",
        production_coeff="1.2",
        a2_24h_liquid="20.0",
        liquid2="10.0",
        oil_volume="8.5",
        fluctuation_range="±0.3",
        shutdown_time="2h",
        theory_diff="0.5",
        theory_displacement="9.0",
        k_value="0.95",
        daily_liquid="25.0",
        daily_oil="8.0",
        well_times="1",
        production_time="23",
        total_oil="500.5"
    )

    from database.db_schema import OilWellDatas

    with SessionLocal() as db:
        oil_well = db.query(Well).filter_by(well_code="油井-D2").first()
        if not oil_well:
            print("油井-D2 不存在，请先插入油井")
        else:
            oil_report = OilWellDatas(**oil_rpt, well_id=oil_well.id)
            db.add(oil_report)
            db.commit()
            print(f"油井日报已写入，id={oil_report.id}")

    # === 6. 层级查询示例 ===

    # ① 作业区 -> 班组
    teams = list_children("area", "作业区D")
    print("班组列表：", [t.team_name for t in teams])

    # ② 班组 -> 计量间
    rooms = list_children("team", "注采十班")
    print("计量间：", [r.room_no for r in rooms])

    # ③ 计量间 -> 报
    baos = list_children("room", "106号")
    print("报类型：", [b.bao_typeid for b in baos])  # 用 bao_typeid 替换 bao_type

    # ④ 报 -> 井（取水报）或平台（油报）
    for bao in baos:
        if bao.bao_typeid == "水报":
            wells = list_children("bao", bao.id)  # 用主键 id 传参
            print("水井：", [w.well_code for w in wells])
        elif bao.bao_typeid == "油报":
            platforms = list_children("bao", bao.id)
            print("平台：", [p.platformer_id for p in platforms])  # 用 platformer_id 替换 platform_name
            for p in platforms:
                wells = list_children("platform", p.id)  # 用主键 id 传参
                print(f"平台 {p.platformer_id} 下油井：", [w.well_code for w in wells])

    # ⑤ 水井 -> 日报
    reports = list_children("well", "水井-D1")
    print("日报数量：", len(reports))

    # === 7. 通过序列查找示例 ===
    # 查找序列：作业区D -> 注采十班 -> 106号 -> 水报 -> 水井-D1 -> 今日日报
    seq = [
        "作业区D",
        "注采十班",
        "106号",
        "水报",
        "水井-D1",
        date.today()
    ]
    daily_report = find_by_sequence(seq)
    print("通过序列查找到的日报：", daily_report)
