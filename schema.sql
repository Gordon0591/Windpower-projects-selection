-- ============================================================
-- 中国风电项目信息收集系统 — 数据库建表脚本
-- 目标: PostgreSQL 15+
-- 执行: psql -h <host> -U <user> -d <dbname> -f schema.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. 字典表
-- ============================================================

-- 省份（按大区分组）
CREATE TABLE provinces (
    id         SMALLINT PRIMARY KEY,
    name       VARCHAR(20) NOT NULL,
    region     VARCHAR(10) NOT NULL,   -- 东北/华北/华东/华南/华中/西北/西南
    sort_order SMALLINT DEFAULT 0
);
COMMENT ON TABLE provinces IS '省份字典';

INSERT INTO provinces VALUES
  (11, '辽宁',   '东北', 1),  (12, '吉林',   '东北', 2),  (13, '黑龙江', '东北', 3),
  (21, '河北',   '华北', 4),  (22, '山西',   '华北', 5),  (23, '内蒙古', '华北', 6),
  (31, '江苏',   '华东', 7),  (32, '浙江',   '华东', 8),  (33, '安徽',   '华东', 9),
  (34, '福建',   '华东', 10), (35, '江西',   '华东', 11), (36, '山东',   '华东', 12),
  (41, '河南',   '华中', 13), (42, '湖北',   '华中', 14), (43, '湖南',   '华中', 15),
  (51, '广东',   '华南', 16), (52, '广西',   '华南', 17), (53, '海南',   '华南', 18),
  (61, '四川',   '西南', 19), (62, '贵州',   '西南', 20), (63, '云南',   '西南', 21),
  (64, '西藏',   '西南', 22),
  (71, '陕西',   '西北', 23), (72, '甘肃',   '西北', 24), (73, '青海',   '西北', 25),
  (74, '宁夏',   '西北', 26), (75, '新疆',   '西北', 27),
  (81, '台湾',   '华东', 28), (82, '香港',   '华南', 29), (83, '澳门',   '华南', 30),
  -- 海域（海上风电不属特定省份时使用）
  (90, '渤海海域', '海域', 31), (91, '黄海海域', '海域', 32),
  (92, '东海海域', '海域', 33), (93, '南海海域', '海域', 34);


-- 项目类型
CREATE TABLE project_types (
    id   SMALLINT PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(20) NOT NULL
);
COMMENT ON TABLE project_types IS '项目类型: 陆上风电 / 海上风电';

INSERT INTO project_types VALUES
  (1, 'onshore',  '陆上风电'),
  (2, 'offshore', '海上风电');


-- 项目状态（按生命周期顺序）
CREATE TABLE project_statuses (
    id         SMALLINT PRIMARY KEY,
    code       VARCHAR(20) NOT NULL UNIQUE,
    name       VARCHAR(20) NOT NULL,
    sort_order SMALLINT DEFAULT 0
);
COMMENT ON TABLE project_statuses IS '项目状态（生命周期: 核准→招标→在建→并网→完工）';

INSERT INTO project_statuses VALUES
  (1, 'planned',         '规划',     0),
  (2, 'approved',        '核准',     1),
  (3, 'bidding',         '招标',     2),
  (4, 'construction',    '在建',     3),
  (5, 'grid_connected',  '并网',     4),
  (6, 'completed',       '完工',     5),
  (7, 'shelved',         '搁置',     6),
  (8, 'cancelled',       '取消',     7);


-- 塔筒构造类型
CREATE TABLE tower_types (
    id   SMALLINT PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(20) NOT NULL
);
COMMENT ON TABLE tower_types IS '塔筒构造: 钢塔 / 混塔';

INSERT INTO tower_types VALUES
  (1, 'steel',   '钢塔'),
  (2, 'hybrid',  '混塔'),
  (3, 'unknown', '待确认');


-- 数据源
CREATE TABLE data_sources (
    id                   SMALLINT PRIMARY KEY,
    name                 VARCHAR(50)  NOT NULL,
    type                 VARCHAR(20)  NOT NULL,  -- govt, bidding_platform, industry_media, wechat, corporate
    base_url             VARCHAR(200),
    scraper_module       VARCHAR(50),
    is_active            BOOLEAN DEFAULT TRUE,
    scrape_interval_min  INT DEFAULT 360,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE data_sources IS '数据源注册表';

INSERT INTO data_sources VALUES
  (1,  '北极星风力发电网',        'industry_media',    'https://fd.bjx.com.cn/',          'bjx_scraper',           TRUE, 120),
  (2,  '每日风电',               'wechat',             NULL,                               'daily_wind_scraper',    TRUE, 360),
  (3,  '海上风电观察',            'wechat',             NULL,                               'offshore_watch',        TRUE, 360),
  (4,  '中国招标投标公共服务平台',  'bidding_platform',  'http://www.cebpubservice.com/',   'cebpub_scraper',        TRUE, 180),
  (5,  '全国投资项目在线审批平台',  'govt',              'https://www.tzxm.gov.cn/',         'tzxm_scraper',          TRUE, 360),
  (6,  '国家能源局',              'govt',               'http://www.nea.gov.cn/',           'nea_scraper',           TRUE, 720),
  (7,  '风能产业',               'wechat',             NULL,                               'wind_energy_scraper',   TRUE, 360),
  (8,  '龙船风电网',              'industry_media',    'https://wind.shipxy.com/',          'shipxy_scraper',        TRUE, 180),
  (9,  '国际风力发电网',           'industry_media',    'https://wind.in-en.com/',           'inen_scraper',          TRUE, 180);


-- ============================================================
-- 2. 核心业务表
-- ============================================================

-- 风电项目主表
CREATE TABLE projects (
    id                     BIGSERIAL PRIMARY KEY,
    name                   VARCHAR(300) NOT NULL,
    province_id            SMALLINT     NOT NULL REFERENCES provinces(id),
    project_type_id        SMALLINT     NOT NULL REFERENCES project_types(id),
    capacity_mw            NUMERIC(9,2) NOT NULL CHECK (capacity_mw > 0),
    turbine_count          INT          CHECK (turbine_count IS NULL OR turbine_count > 0),
    unit_capacity_mw       NUMERIC(6,2) CHECK (unit_capacity_mw IS NULL OR unit_capacity_mw > 0),
    tower_type_id          SMALLINT     DEFAULT 3 REFERENCES tower_types(id),
    status_id              SMALLINT     NOT NULL REFERENCES project_statuses(id),
    owner                  VARCHAR(300),
    turbine_supplier       VARCHAR(300),
    investment_bn          NUMERIC(10,2) CHECK (investment_bn IS NULL OR investment_bn > 0),
    approval_date          DATE,
    bid_date               DATE,
    construction_start_date DATE,
    completion_date        DATE,
    planned_cod_date       DATE,
    description            TEXT,
    is_verified            BOOLEAN DEFAULT FALSE,
    created_at             TIMESTAMPTZ DEFAULT NOW(),
    updated_at             TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_project UNIQUE (name, province_id)
);
COMMENT ON TABLE projects IS '风电项目主表';
COMMENT ON COLUMN projects.capacity_mw             IS '总装机容量 (MW)';
COMMENT ON COLUMN projects.turbine_count           IS '风机台数';
COMMENT ON COLUMN projects.unit_capacity_mw        IS '单机容量 (MW)';
COMMENT ON COLUMN projects.tower_type_id           IS '塔筒构造: 1=钢塔 2=混塔 3=待确认';
COMMENT ON COLUMN projects.investment_bn           IS '投资金额 (亿元)';
COMMENT ON COLUMN projects.approval_date           IS '核准批复日期';
COMMENT ON COLUMN projects.bid_date                IS '招标/中标公示日期';
COMMENT ON COLUMN projects.construction_start_date IS '主体工程开工日期';
COMMENT ON COLUMN projects.completion_date         IS '全容量并网/完工日期';
COMMENT ON COLUMN projects.planned_cod_date        IS '计划并网日期';


-- 项目信息来源关联
CREATE TABLE project_sources (
    id          BIGSERIAL PRIMARY KEY,
    project_id  BIGINT       NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_id   SMALLINT     NOT NULL REFERENCES data_sources(id),
    source_url  VARCHAR(1000),
    captured_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_project_source_url UNIQUE (project_id, source_id, source_url)
);
COMMENT ON TABLE project_sources IS '项目与数据源的多对多关联';


-- 项目状态变更日志
CREATE TABLE project_status_logs (
    id            BIGSERIAL PRIMARY KEY,
    project_id    BIGINT    NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    old_status_id SMALLINT  REFERENCES project_statuses(id),
    new_status_id SMALLINT  NOT NULL REFERENCES project_statuses(id),
    changed_at    TIMESTAMPTZ DEFAULT NOW(),
    source_id     SMALLINT  REFERENCES data_sources(id),
    remark        VARCHAR(500)
);
COMMENT ON TABLE project_status_logs IS '项目全生命周期状态变更记录';


-- 采集运行日志
CREATE TABLE scrape_logs (
    id             BIGSERIAL PRIMARY KEY,
    data_source_id SMALLINT    NOT NULL REFERENCES data_sources(id),
    started_at     TIMESTAMPTZ NOT NULL,
    finished_at    TIMESTAMPTZ,
    items_scraped  INT DEFAULT 0,
    items_new      INT DEFAULT 0,
    items_updated  INT DEFAULT 0,
    status         VARCHAR(10) DEFAULT 'running',  -- running, success, failed
    error_message  TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE scrape_logs IS '爬虫采集运行日志';


-- ============================================================
-- 3. 索引
-- ============================================================

-- 项目查询索引
CREATE INDEX idx_projects_province        ON projects(province_id);
CREATE INDEX idx_projects_type            ON projects(project_type_id);
CREATE INDEX idx_projects_status          ON projects(status_id);
CREATE INDEX idx_projects_tower_type      ON projects(tower_type_id);
CREATE INDEX idx_projects_approval_date   ON projects(approval_date DESC);
CREATE INDEX idx_projects_bid_date        ON projects(bid_date DESC);
CREATE INDEX idx_projects_construction    ON projects(construction_start_date DESC);
CREATE INDEX idx_projects_completion      ON projects(completion_date DESC);
CREATE INDEX idx_projects_planned_cod     ON projects(planned_cod_date DESC);
CREATE INDEX idx_projects_capacity        ON projects(capacity_mw);
CREATE INDEX idx_projects_owner           ON projects(owner);
CREATE INDEX idx_projects_supplier        ON projects(turbine_supplier);
CREATE INDEX idx_projects_verified        ON projects(is_verified) WHERE is_verified = TRUE;
CREATE INDEX idx_projects_created         ON projects(created_at DESC);

-- 复合索引（覆盖高频组合查询）
CREATE INDEX idx_projects_type_status     ON projects(project_type_id, status_id);
CREATE INDEX idx_projects_prov_type       ON projects(province_id, project_type_id);
CREATE INDEX idx_projects_prov_status     ON projects(province_id, status_id);
CREATE INDEX idx_projects_type_tower      ON projects(project_type_id, tower_type_id);

-- 全文搜索（项目名称 + 业主 + 描述）
CREATE INDEX idx_projects_search ON projects
    USING GIN (to_tsvector('simple',
        coalesce(name,'') || ' ' ||
        coalesce(owner,'') || ' ' ||
        coalesce(turbine_supplier,'') || ' ' ||
        coalesce(description,'')
    ));

-- 来源关联索引
CREATE INDEX idx_project_sources_project  ON project_sources(project_id);
CREATE INDEX idx_project_sources_source   ON project_sources(source_id);

-- 状态日志索引
CREATE INDEX idx_status_logs_project      ON project_status_logs(project_id, changed_at DESC);
CREATE INDEX idx_status_logs_date         ON project_status_logs(changed_at DESC);

-- 采集日志索引
CREATE INDEX idx_scrape_logs_source       ON scrape_logs(data_source_id, started_at DESC);
CREATE INDEX idx_scrape_logs_status       ON scrape_logs(status) WHERE status = 'running';


-- ============================================================
-- 4. 触发器：自动更新 updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- 5. 视图
-- ============================================================

-- 项目列表视图（JOIN 好字典表，方便直接查询）
CREATE VIEW v_projects AS
SELECT
    p.id,
    p.name,
    p.province_id,
    prov.name        AS province_name,
    prov.region      AS province_region,
    p.project_type_id,
    pt.code          AS project_type_code,
    pt.name          AS project_type_name,
    p.capacity_mw,
    p.turbine_count,
    p.unit_capacity_mw,
    p.tower_type_id,
    tt.code          AS tower_type_code,
    tt.name          AS tower_type_name,
    p.status_id,
    ps.code          AS status_code,
    ps.name          AS status_name,
    p.owner,
    p.turbine_supplier,
    p.investment_bn,
    p.approval_date,
    p.bid_date,
    p.construction_start_date,
    p.completion_date,
    p.planned_cod_date,
    p.description,
    p.is_verified,
    p.created_at,
    p.updated_at
FROM projects p
JOIN provinces        prov ON p.province_id = prov.id
JOIN project_types    pt   ON p.project_type_id = pt.id
JOIN project_statuses ps   ON p.status_id = ps.id
JOIN tower_types      tt   ON p.tower_type_id = tt.id;


-- 各省汇总统计视图
CREATE VIEW v_stats_by_province AS
SELECT
    prov.id            AS province_id,
    prov.name          AS province_name,
    prov.region        AS province_region,
    COUNT(p.id)        AS project_count,
    COALESCE(SUM(p.capacity_mw), 0)                         AS total_capacity_mw,
    COALESCE(SUM(p.turbine_count), 0)                       AS total_turbines,
    COALESCE(SUM(p.capacity_mw) FILTER (WHERE pt.code = 'onshore'), 0)  AS onshore_mw,
    COALESCE(SUM(p.capacity_mw) FILTER (WHERE pt.code = 'offshore'), 0) AS offshore_mw,
    COALESCE(SUM(p.capacity_mw) FILTER (WHERE tt.code = 'steel'), 0)   AS steel_tower_mw,
    COALESCE(SUM(p.capacity_mw) FILTER (WHERE tt.code = 'hybrid'), 0)  AS hybrid_tower_mw
FROM provinces prov
LEFT JOIN projects p ON p.province_id = prov.id
LEFT JOIN project_types pt ON p.project_type_id = pt.id
LEFT JOIN tower_types tt ON p.tower_type_id = tt.id
GROUP BY prov.id, prov.name, prov.region
ORDER BY total_capacity_mw DESC;


-- 年度趋势统计视图
CREATE VIEW v_stats_by_year AS
SELECT
    EXTRACT(YEAR FROM approval_date)::INT AS year,
    'approved'                            AS metric,
    COUNT(*)                              AS project_count,
    COALESCE(SUM(capacity_mw), 0)         AS capacity_mw,
    COALESCE(SUM(turbine_count), 0)       AS turbine_count
FROM projects WHERE approval_date IS NOT NULL
GROUP BY EXTRACT(YEAR FROM approval_date)

UNION ALL

SELECT
    EXTRACT(YEAR FROM construction_start_date)::INT,
    'construction_started',
    COUNT(*),
    COALESCE(SUM(capacity_mw), 0),
    COALESCE(SUM(turbine_count), 0)
FROM projects WHERE construction_start_date IS NOT NULL
GROUP BY EXTRACT(YEAR FROM construction_start_date)

UNION ALL

SELECT
    EXTRACT(YEAR FROM completion_date)::INT,
    'completed',
    COUNT(*),
    COALESCE(SUM(capacity_mw), 0),
    COALESCE(SUM(turbine_count), 0)
FROM projects WHERE completion_date IS NOT NULL
GROUP BY EXTRACT(YEAR FROM completion_date);

COMMIT;
