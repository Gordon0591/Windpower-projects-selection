"""种子数据 — 首次启动时自动插入"""

from models import DataSource, ProjectStatus, ProjectType, Province, TowerType


def seed(db):
    """插入字典种子数据（幂等：已存在则跳过）"""

    # 省份
    provinces = [
        (11, "辽宁", "东北"), (12, "吉林", "东北"), (13, "黑龙江", "东北"),
        (21, "河北", "华北"), (22, "山西", "华北"), (23, "内蒙古", "华北"),
        (31, "江苏", "华东"), (32, "浙江", "华东"), (33, "安徽", "华东"),
        (34, "福建", "华东"), (35, "江西", "华东"), (36, "山东", "华东"),
        (41, "河南", "华中"), (42, "湖北", "华中"), (43, "湖南", "华中"),
        (51, "广东", "华南"), (52, "广西", "华南"), (53, "海南", "华南"),
        (61, "四川", "西南"), (62, "贵州", "西南"), (63, "云南", "西南"),
        (64, "西藏", "西南"),
        (71, "陕西", "西北"), (72, "甘肃", "西北"), (73, "青海", "西北"),
        (74, "宁夏", "西北"), (75, "新疆", "西北"),
        (90, "渤海海域", "海域"), (91, "黄海海域", "海域"),
        (92, "东海海域", "海域"), (93, "南海海域", "海域"),
    ]
    for pid, name, region in provinces:
        if not db.get(Province, pid):
            db.add(Province(id=pid, name=name, region=region))

    # 项目类型
    types = [(1, "onshore", "陆上风电"), (2, "offshore", "海上风电")]
    for tid, code, name in types:
        if not db.get(ProjectType, tid):
            db.add(ProjectType(id=tid, code=code, name=name))

    # 状态
    statuses = [
        (1, "planned", "规划"), (2, "approved", "核准"), (3, "bidding", "招标"),
        (4, "construction", "在建"), (5, "grid_connected", "并网"),
        (6, "completed", "完工"), (7, "shelved", "搁置"), (8, "cancelled", "取消"),
    ]
    for sid, code, name in statuses:
        if not db.get(ProjectStatus, sid):
            db.add(ProjectStatus(id=sid, code=code, name=name))

    # 塔筒
    towers = [(1, "steel", "钢塔"), (2, "hybrid", "混塔"), (3, "unknown", "待确认")]
    for tid, code, name in towers:
        if not db.get(TowerType, tid):
            db.add(TowerType(id=tid, code=code, name=name))

    # 数据源
    sources = [
        (1, "北极星风力发电网", "industry_media", "https://fd.bjx.com.cn/"),
        (2, "每日风电", "wechat", None),
        (3, "海上风电观察", "wechat", None),
        (4, "中国招标投标公共服务平台", "bidding_platform", "http://www.cebpubservice.com/"),
        (5, "全国投资项目在线审批平台", "govt", "https://www.tzxm.gov.cn/"),
        (6, "国家能源局", "govt", "http://www.nea.gov.cn/"),
        (7, "风能产业", "wechat", None),
        (8, "龙船风电网", "industry_media", "https://wind.shipxy.com/"),
        (9, "国际风力发电网", "industry_media", "https://wind.in-en.com/"),
    ]
    for sid, name, stype, url in sources:
        if not db.get(DataSource, sid):
            db.add(DataSource(id=sid, name=name, type=stype, base_url=url))

    db.commit()
    print("✅ Seed data inserted")
