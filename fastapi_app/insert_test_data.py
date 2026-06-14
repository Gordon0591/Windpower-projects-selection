#!/usr/bin/env python3
"""插入测试数据 — 30个真实感的风电项目"""

from datetime import date
from database import SessionLocal
from models import Project, ProjectSource, ProjectStatusLog


PROJECTS = [
    # ── 海上风电 ──
    {"name": "国家能源集团广东湛江徐闻海上风电场一期工程", "province_id": 51, "project_type_id": 2,
     "capacity_mw": 500, "turbine_count": 56, "unit_capacity_mw": 8.93, "tower_type_id": 1,
     "status_id": 4, "owner": "国家能源集团", "turbine_supplier": "明阳智能",
     "investment_bn": 45.0, "approval_date": date(2024,8,15), "bid_date": date(2024,11,20),
     "construction_start_date": date(2025,3,1), "planned_cod_date": date(2026,6,30),
     "description": "位于湛江市徐闻县东部海域，中心离岸距离约27km，场址水深15-25m。安装56台MySE8.5-216风机。"},

    {"name": "中广核广东汕尾甲子海上风电场二期工程", "province_id": 51, "project_type_id": 2,
     "capacity_mw": 900, "turbine_count": 90, "unit_capacity_mw": 10.0, "tower_type_id": 1,
     "status_id": 5, "owner": "中广核", "turbine_supplier": "东方风电",
     "investment_bn": 85.0, "approval_date": date(2023,6,1), "bid_date": date(2023,10,15),
     "construction_start_date": date(2024,2,1), "completion_date": date(2025,12,20),
     "planned_cod_date": date(2025,12,31),
     "description": "汕尾甲子海域，水深20-35m，安装90台10MW风机，年利用小时数约3500h。"},

    {"name": "三峡能源江苏大丰海上风电场三期", "province_id": 31, "project_type_id": 2,
     "capacity_mw": 800, "turbine_count": 64, "unit_capacity_mw": 12.5, "tower_type_id": 1,
     "status_id": 4, "owner": "三峡能源", "turbine_supplier": "金风科技",
     "investment_bn": 72.0, "approval_date": date(2024,5,10), "bid_date": date(2024,9,1),
     "construction_start_date": date(2025,1,15), "planned_cod_date": date(2026,9,30),
     "description": "江苏大丰海域，安装64台GWH252-12.5MW风机，配套建设220kV海上升压站。"},

    {"name": "华能海南洋浦海上风电项目", "province_id": 53, "project_type_id": 2,
     "capacity_mw": 600, "turbine_count": 37, "unit_capacity_mw": 16.2, "tower_type_id": 1,
     "status_id": 3, "owner": "华能集团", "turbine_supplier": "远景能源",
     "investment_bn": 58.0, "approval_date": date(2025,1,20),
     "planned_cod_date": date(2027,3,31),
     "description": "海南洋浦海域，中国首个16MW级以上批量海上风电项目。"},

    {"name": "龙源电力福建莆田南日岛海上风电场四期", "province_id": 34, "project_type_id": 2,
     "capacity_mw": 400, "turbine_count": 25, "unit_capacity_mw": 16.0, "tower_type_id": 1,
     "status_id": 2, "owner": "龙源电力", "turbine_supplier": "中国海装",
     "investment_bn": 38.0, "approval_date": date(2025,4,15),
     "planned_cod_date": date(2027,6,30),
     "description": "福建莆田南日岛海域，水深20-40m，安装25台H260-16MW风机。"},

    # ── 陆上风电（钢塔） ──
    {"name": "华能内蒙古乌兰察布风电基地一期", "province_id": 23, "project_type_id": 1,
     "capacity_mw": 1500, "turbine_count": 200, "unit_capacity_mw": 7.5, "tower_type_id": 1,
     "status_id": 5, "owner": "华能集团", "turbine_supplier": "运达股份",
     "investment_bn": 90.0, "approval_date": date(2022,8,1), "bid_date": date(2023,1,15),
     "construction_start_date": date(2023,6,1), "completion_date": date(2025,6,30),
     "planned_cod_date": date(2025,6,30),
     "description": "内蒙古乌兰察布千万千瓦级风电基地，一期1500MW，安装200台WD156-7500风机。"},

    {"name": "国家电投新疆哈密风电基地扩建项目", "province_id": 75, "project_type_id": 1,
     "capacity_mw": 800, "turbine_count": 120, "unit_capacity_mw": 6.67, "tower_type_id": 1,
     "status_id": 4, "owner": "国家电投", "turbine_supplier": "金风科技",
     "investment_bn": 48.0, "approval_date": date(2024,9,1),
     "construction_start_date": date(2025,4,1), "planned_cod_date": date(2026,6,30),
     "description": "新疆哈密三塘湖风区，安装120台GWH191-6.67MW风机。"},

    {"name": "大唐吉林白城风电项目", "province_id": 12, "project_type_id": 1,
     "capacity_mw": 300, "turbine_count": 48, "unit_capacity_mw": 6.25, "tower_type_id": 1,
     "status_id": 2, "owner": "大唐集团", "turbine_supplier": "三一重能",
     "investment_bn": 18.0, "approval_date": date(2025,3,10),
     "planned_cod_date": date(2026,9,30),
     "description": "吉林白城通榆县，安装48台SI-193-6.25MW风机，钢塔筒。"},

    {"name": "中核集团甘肃酒泉风电项目", "province_id": 72, "project_type_id": 1,
     "capacity_mw": 500, "turbine_count": 80, "unit_capacity_mw": 6.25, "tower_type_id": 1,
     "status_id": 4, "owner": "中核集团", "turbine_supplier": "电气风电",
     "investment_bn": 30.0, "approval_date": date(2024,6,15),
     "construction_start_date": date(2025,2,1), "planned_cod_date": date(2026,3,31),
     "description": "甘肃酒泉瓜州县，安装80台EW6.25-202风机，钢塔。"},

    {"name": "华润电力宁夏吴忠风电项目", "province_id": 74, "project_type_id": 1,
     "capacity_mw": 200, "turbine_count": 32, "unit_capacity_mw": 6.25, "tower_type_id": 1,
     "status_id": 5, "owner": "华润电力", "turbine_supplier": "运达股份",
     "investment_bn": 12.0, "approval_date": date(2023,10,1), "bid_date": date(2024,2,1),
     "construction_start_date": date(2024,5,1), "completion_date": date(2025,9,15),
     "planned_cod_date": date(2025,9,30),
     "description": "宁夏吴忠市盐池县，安装32台WD164-6250风机。"},

    # ── 陆上风电（混塔） ── 混塔趋势项目
    {"name": "三峡能源河南商丘风电项目", "province_id": 41, "project_type_id": 1,
     "capacity_mw": 300, "turbine_count": 50, "unit_capacity_mw": 6.0, "tower_type_id": 2,
     "status_id": 4, "owner": "三峡能源", "turbine_supplier": "明阳智能",
     "investment_bn": 19.5, "approval_date": date(2024,7,1),
     "construction_start_date": date(2025,3,15), "planned_cod_date": date(2026,5,31),
     "description": "河南商丘，平原高塔场景，轮毂高度170m，采用钢混混合塔筒（混塔），安装50台MySE6.0-200风机。"},

    {"name": "华电山东菏泽风电项目", "province_id": 36, "project_type_id": 1,
     "capacity_mw": 250, "turbine_count": 40, "unit_capacity_mw": 6.25, "tower_type_id": 2,
     "status_id": 4, "owner": "华电集团", "turbine_supplier": "远景能源",
     "investment_bn": 16.0, "approval_date": date(2024,5,20),
     "construction_start_date": date(2025,1,10), "planned_cod_date": date(2026,1,31),
     "description": "山东菏泽平原风电，轮毂高度165m，混塔方案，安装40台EN-192/6.25风机。"},

    {"name": "国家能源集团安徽阜阳风电项目", "province_id": 33, "project_type_id": 1,
     "capacity_mw": 200, "turbine_count": 32, "unit_capacity_mw": 6.25, "tower_type_id": 2,
     "status_id": 5, "owner": "国家能源集团", "turbine_supplier": "金风科技",
     "investment_bn": 13.0, "approval_date": date(2023,8,1), "bid_date": date(2024,1,15),
     "construction_start_date": date(2024,4,1), "completion_date": date(2025,10,20),
     "planned_cod_date": date(2025,10,31),
     "description": "安徽阜阳，中东南部低风速区域，混塔方案轮毂高度160m，安装32台GWH191-6.25风机。"},

    {"name": "大唐河南驻马店风电项目", "province_id": 41, "project_type_id": 1,
     "capacity_mw": 150, "turbine_count": 24, "unit_capacity_mw": 6.25, "tower_type_id": 2,
     "status_id": 3, "owner": "大唐集团", "turbine_supplier": "三一重能",
     "investment_bn": 9.8, "approval_date": date(2025,2,1),
     "planned_cod_date": date(2026,10,31),
     "description": "河南驻马店，混塔方案，轮毂高度165m，安装24台SI-193-6.25MW风机。"},

    # ── 今年核准/招标/开工项目 ──
    {"name": "84亿元！黑龙江核准1.6GW风电项目", "province_id": 13, "project_type_id": 1,
     "capacity_mw": 1600, "turbine_count": 220, "unit_capacity_mw": 7.27, "tower_type_id": 1,
     "status_id": 2, "owner": "京能国际/中国一重/龙煤集团", "turbine_supplier": None,
     "investment_bn": 84.0, "approval_date": date(2025,6,1),
     "planned_cod_date": date(2027,12,31),
     "description": "黑龙江省2025年风电大基地项目，涉及京能国际、中国一重、龙煤集团三家业主联合开发。"},

    {"name": "三峡能源内蒙古70万千瓦风电项目", "province_id": 23, "project_type_id": 1,
     "capacity_mw": 700, "turbine_count": 100, "unit_capacity_mw": 7.0, "tower_type_id": 1,
     "status_id": 2, "owner": "三峡能源", "turbine_supplier": None,
     "investment_bn": 42.0, "approval_date": date(2025,5,15),
     "planned_cod_date": date(2027,6,30),
     "description": "内蒙古自治区2025年保障性并网风电项目。"},

    {"name": "中广核广东阳江帆石海上风电场一期", "province_id": 51, "project_type_id": 2,
     "capacity_mw": 1000, "turbine_count": 62, "unit_capacity_mw": 16.13, "tower_type_id": 1,
     "status_id": 3, "owner": "中广核", "turbine_supplier": "明阳智能",
     "investment_bn": 95.0, "approval_date": date(2024,11,1), "bid_date": date(2025,2,20),
     "planned_cod_date": date(2027,9,30),
     "description": "阳江帆石海域，水深30-40m，安装62台MySE16-260风机，单机16MW级。"},

    {"name": "龙源电力江苏射阳100万千瓦海上风电项目", "province_id": 31, "project_type_id": 2,
     "capacity_mw": 1000, "turbine_count": 80, "unit_capacity_mw": 12.5, "tower_type_id": 1,
     "status_id": 3, "owner": "龙源电力", "turbine_supplier": "电气风电",
     "investment_bn": 92.0, "approval_date": date(2024,8,1), "bid_date": date(2025,1,10),
     "construction_start_date": date(2025,5,1), "planned_cod_date": date(2027,3,31),
     "description": "江苏射阳海域，安装80台EW12.5-252风机。"},

    {"name": "甘肃定西300MW风电项目", "province_id": 72, "project_type_id": 1,
     "capacity_mw": 300, "turbine_count": 48, "unit_capacity_mw": 6.25, "tower_type_id": 1,
     "status_id": 2, "owner": "华能集团", "turbine_supplier": None,
     "investment_bn": 18.0, "approval_date": date(2025,5,1),
     "planned_cod_date": date(2026,12,31),
     "description": "甘肃省定西市2025年风电竞配项目，华能中标。"},

    # ── 更多完工项目 ──
    {"name": "国家电投山东海阳海上风电项目", "province_id": 36, "project_type_id": 2,
     "capacity_mw": 300, "turbine_count": 30, "unit_capacity_mw": 10.0, "tower_type_id": 1,
     "status_id": 5, "owner": "国家电投", "turbine_supplier": "中国海装",
     "investment_bn": 28.0, "approval_date": date(2022,6,1), "bid_date": date(2022,11,1),
     "construction_start_date": date(2023,2,1), "completion_date": date(2024,12,15),
     "planned_cod_date": date(2024,12,31),
     "description": "山东海阳海域，山东省首批海上风电项目，安装30台H220-10MW风机。"},

    {"name": "华能广西桂林风电项目", "province_id": 52, "project_type_id": 1,
     "capacity_mw": 200, "turbine_count": 50, "unit_capacity_mw": 4.0, "tower_type_id": 2,
     "status_id": 5, "owner": "华能集团", "turbine_supplier": "明阳智能",
     "investment_bn": 14.0, "approval_date": date(2022,5,1), "construction_start_date": date(2023,3,1),
     "completion_date": date(2024,9,20), "planned_cod_date": date(2024,9,30),
     "description": "广西北部山区风电，混塔方案轮毂高度140m，安装50台MySE4.0-166风机。"},

    {"name": "金风科技河北张家口风电项目", "province_id": 21, "project_type_id": 1,
     "capacity_mw": 150, "turbine_count": 30, "unit_capacity_mw": 5.0, "tower_type_id": 1,
     "status_id": 1, "owner": "金风科技", "turbine_supplier": "金风科技",
     "investment_bn": 9.0, "approval_date": None,
     "description": "河北张家口坝上地区，规划阶段，金风自建风电项目。"},

    # ── 更多混塔项目（展示趋势）──
    {"name": "华润电力湖北襄阳风电项目", "province_id": 42, "project_type_id": 1,
     "capacity_mw": 200, "turbine_count": 32, "unit_capacity_mw": 6.25, "tower_type_id": 2,
     "status_id": 4, "owner": "华润电力", "turbine_supplier": "运达股份",
     "investment_bn": 13.0, "approval_date": date(2024,10,1),
     "construction_start_date": date(2025,4,15), "planned_cod_date": date(2026,8,31),
     "description": "湖北襄阳，混塔方案轮毂高度165m，低风速高切变区域。"},

    {"name": "中广核湖南岳阳风电项目", "province_id": 43, "project_type_id": 1,
     "capacity_mw": 100, "turbine_count": 16, "unit_capacity_mw": 6.25, "tower_type_id": 2,
     "status_id": 5, "owner": "中广核", "turbine_supplier": "三一重能",
     "investment_bn": 6.5, "approval_date": date(2023,7,1), "construction_start_date": date(2024,1,1),
     "completion_date": date(2025,8,15), "planned_cod_date": date(2025,8,31),
     "description": "湖南岳阳洞庭湖平原，混塔方案，中国内陆首个批量混塔项目。"},

    # ── 搁置/规划项目 ──
    {"name": "华能17MW漂浮式海上风电示范项目", "province_id": 93, "project_type_id": 2,
     "capacity_mw": 34, "turbine_count": 2, "unit_capacity_mw": 17.0, "tower_type_id": 1,
     "status_id": 1, "owner": "华能集团", "turbine_supplier": "中国海装",
     "investment_bn": 5.0, "approval_date": None,
     "description": "南海海域，漂浮式海上风电示范项目，安装2台17MW漂浮式风机，全球最大漂浮式风电。"},

    {"name": "内蒙古5.6MW分散式风电项目（已废止）", "province_id": 23, "project_type_id": 1,
     "capacity_mw": 5.6, "turbine_count": 1, "unit_capacity_mw": 5.6, "tower_type_id": 3,
     "status_id": 8, "owner": "地方企业", "turbine_supplier": None,
     "investment_bn": 0.35, "approval_date": date(2022,3,1),
     "description": "内蒙古分散式风电项目，因土地问题被废止。"},
]

STATUS_MAP = {
    1: "规划", 2: "核准", 3: "招标", 4: "在建",
    5: "并网", 6: "完工", 7: "搁置", 8: "取消",
}


def insert():
    db = SessionLocal()
    try:
        for i, p in enumerate(PROJECTS):
            # 跳过已存在的
            from sqlalchemy import select
            existing = db.execute(
                select(Project).where(
                    Project.name == p["name"],
                    Project.province_id == p["province_id"],
                )
            ).scalar_one_or_none()
            if existing:
                print(f"  跳过(已存在): {p['name'][:40]}...")
                continue

            project = Project(**p)
            db.add(project)
            db.flush()

            # 状态变更日志
            status_id = p["status_id"]
            notes = [
                (None, "项目首次收录"),
                (status_id, f"当前状态: {STATUS_MAP.get(status_id, '未知')}"),
            ]
            for sid, remark in notes:
                db.add(ProjectStatusLog(
                    project_id=project.id,
                    new_status_id=sid or status_id,
                    changed_at=p.get("approval_date") or p.get("construction_start_date") or date(2024,1,1),
                    remark=remark,
                ))

            # 来源关联
            db.add(ProjectSource(
                project_id=project.id,
                source_id=(i % 9) + 1,
                source_url=f"https://fd.bjx.com.cn/news/test_{i+1}",
            ))

            print(f"  ✅ {p['name'][:50]}...")

        db.commit()
        print(f"\n✅ 共插入 {len(PROJECTS)} 个测试项目")
    finally:
        db.close()


if __name__ == "__main__":
    insert()
