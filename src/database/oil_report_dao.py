from sqlalchemy.orm import Session
from src.database.db_oil_schema import OilWellReports, engine
from datetime import date, timedelta
import datetime as dt


class MySQLManager:
    def __init__(self):
        self.engine = engine
    def clear_current_table(self):
        """清空内存中的报表数据（原清空oil_well_datas表功能调整）"""
        # 实际项目中可以在这里添加清空内存数据的逻辑
        return True, "已清空当前报表数据"

    def fetch_previous_day_report(self, well_code: str, platform: str, target_date: date) -> dict:
        """查询同平台、同井号的前一天历史记录"""
        with Session(engine) as session:
            try:
                previous_day = target_date - timedelta(days=1)
                record = session.query(OilWellReports).filter(
                    OilWellReports.well_code == well_code,
                    OilWellReports.platform == platform,
                    OilWellReports.create_time == previous_day
                ).first()
                return self._to_dict(record) if record else None
            except Exception as e:
                print(f"查询前一天数据失败: {e}")
                return None

    def sync_to_backup(self, reports_data):
        """将内存中的报表数据同步到历史报表"""
        with Session(engine) as session:
            try:
                if not reports_data:
                    return True, "当前表无数据可同步"

                new_count = 0
                update_count = 0
                skip_count = 0

                # 构建历史报表索引：(platform, well_code, create_time) → report_record
                reports_index = {
                    (report.platform, report.well_code, report.create_time): report
                    for report in session.query(OilWellReports).all()
                }

                for data_record in reports_data:
                    # 构建唯一标识元组
                    key = (data_record["platform"], data_record["well_code"], data_record["create_time"])

                    # 检查是否存在匹配的历史记录
                    if key not in reports_index:
                        # 新增记录
                        new_report = OilWellReports(**{
                            k: v for k, v in data_record.items() if k != 'id'
                        })
                        session.add(new_report)
                        new_count += 1
                    else:
                        # 检查是否需要更新
                        report_record = reports_index[key]
                        if self._has_any_differences(data_record, report_record):
                            # 有差异，更新记录
                            for k, v in data_record.items():
                                if k != 'id':
                                    setattr(report_record, k, v)
                            update_count += 1
                        else:
                            # 无差异，跳过
                            skip_count += 1

                session.commit()
                return True, (f"同步完成：\n"
                              f"新增 {new_count} 条，更新 {update_count} 条，\n"
                              f"跳过 {skip_count} 条（内容完全相同）")

            except Exception as e:
                session.rollback()
                return False, f"同步失败：{str(e)}"

    def _has_any_differences(self, data_record, report_record):
        """检查两条记录的所有字段是否有任何不同（排除ID）"""
        for key, value in data_record.items():
            if key == 'id':
                continue
            if key=='well_id':
                continue

            report_val = getattr(report_record, key)

            # 特殊处理日期类型比较
            if isinstance(value, date) and isinstance(report_val, date):
                if value != report_val:
                    return True
                continue

            # 处理None值
            if value is None and report_val is None:
                continue
            if value is None or report_val is None:
                return True

            # 字符串比较
            if str(value).strip() != str(report_val).strip():
                return True

        return False

    def _to_dict(self, obj):
        """ORM对象转字典"""
        if not obj:
            return None
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}