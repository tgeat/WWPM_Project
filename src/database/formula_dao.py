import re
from typing import Iterable

import pymysql

from ..config.db_config import DB_URI
from ..model.formula_model import Formula


def upsert_formulas(formulas: Iterable[Formula]) -> int:
    """将公式数据写入数据库（存在则更新，不存在则插入）"""
    match = re.match(
        r"mysql\+pymysql://(\w+):(\w+)@([\d\.]+):(\d+)/(\w+)\?charset=(\w+)",
        DB_URI,
    )
    if not match:
        raise ValueError("无效的DB_URI格式")

    user, password, host, port, database, charset = match.groups()
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=int(port),
        charset=charset,
    )
    cursor = conn.cursor()

    cursor.execute("SELECT id, formula FROM formula_datas")
    existing = {}
    for id_, formula in cursor.fetchall():
        if "=" not in formula:
            continue
        left_old, right_old = formula.split("=", 1)
        existing[left_old] = (id_, right_old)

    to_update = []
    to_insert = []
    for f in formulas:
        if f.left in existing:
            existing_id, existing_right = existing[f.left]
            if f.right != existing_right:
                to_update.append((f"{f.left}={f.right}", existing_id))
        else:
            to_insert.append((f"{f.left}={f.right}",))

    if to_update:
        cursor.executemany("UPDATE formula_datas SET formula = %s WHERE id = %s", to_update)
    if to_insert:
        cursor.executemany("INSERT INTO formula_datas (formula) VALUES (%s)", to_insert)

    total = len(to_update) + len(to_insert)
    conn.commit()
    cursor.close()
    conn.close()
    return total
