from __future__ import annotations
"""LLM 结构化提取 — 将新闻正文转为项目结构化字段"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# Claude Tool Use 的 JSON Schema
# ══════════════════════════════════════════════════════════

EXTRACT_PROJECT_TOOL = {
    "name": "extract_wind_project",
    "description": "从风电行业新闻中提取项目结构化信息。如果原文不包含风电项目信息，所有字段返回 null。",
    "input_schema": {
        "type": "object",
        "properties": {
            "has_project": {
                "type": "boolean",
                "description": "原文是否包含一个具体的风电项目信息（有项目名称 + 至少一个关键字段如容量/省份/业主）"
            },
            "project_name": {
                "type": ["string", "null"],
                "description": "项目完整名称，如'XX风电场一期工程'"
            },
            "province": {
                "type": ["string", "null"],
                "description": "省份名称，如'广东'、'内蒙古'。海域项目标'南海海域'等"
            },
            "project_type": {
                "type": ["string", "null"],
                "enum": ["onshore", "offshore", None],
                "description": "onshore=陆上风电, offshore=海上风电"
            },
            "capacity_mw": {
                "type": ["number", "null"],
                "description": "总装机容量，单位兆瓦(MW)"
            },
            "turbine_count": {
                "type": ["integer", "null"],
                "description": "风机台数，安装了XX台风机"
            },
            "unit_capacity_mw": {
                "type": ["number", "null"],
                "description": "单台风机容量(MW)，如8.5MW、6.25MW"
            },
            "tower_type": {
                "type": ["string", "null"],
                "enum": ["steel", "hybrid", None],
                "description": "塔筒构造: steel=钢塔, hybrid=混塔(钢混混合塔筒)。原文明确提及'混塔''钢混塔''混合塔''混凝土塔筒'→hybrid; 明确'钢塔''全钢塔'→steel; 未提及→null"
            },
            "status": {
                "type": ["string", "null"],
                "enum": ["planned", "approved", "bidding", "construction", "grid_connected", "completed", None],
                "description": "项目当前状态: planned=规划, approved=核准/批复, bidding=招标/中标, construction=在建/开工/吊装, grid_connected=并网/首批并网, completed=完工/全容量并网"
            },
            "owner": {
                "type": ["string", "null"],
                "description": "业主/开发商名称，如'国家能源集团''华能集团'"
            },
            "turbine_supplier": {
                "type": ["string", "null"],
                "description": "风机整机供应商名称，如'金风科技''明阳智能''远景能源'"
            },
            "investment_bn": {
                "type": ["number", "null"],
                "description": "项目总投资金额，单位亿元"
            },
            "approval_date": {
                "type": ["string", "null"],
                "description": "核准/批复日期，格式 YYYY-MM-DD"
            },
            "bid_date": {
                "type": ["string", "null"],
                "description": "招标公布/中标公示日期"
            },
            "construction_start_date": {
                "type": ["string", "null"],
                "description": "开工日期"
            },
            "completion_date": {
                "type": ["string", "null"],
                "description": "完工/全容量并网日期"
            },
            "planned_cod_date": {
                "type": ["string", "null"],
                "description": "计划并网/投产日期"
            },
        },
        "required": ["has_project"],
    },
}


EXTRACT_PROMPT = """从以下风电行业新闻中提取风电项目信息。

规则:
1. 如果原文确实包含一个具体的风电项目(有项目名称+至少容量或省份)，则提取所有可用字段
2. 如果原文只是行业综述/政策解读/企业动态而不涉及具体项目，设 has_project=false
3. 字段未提及时返回 null，不要编造
4. 容量单位注意转换: 1GW=1000MW, 万千瓦×10=MW
5. 日期统一为 YYYY-MM-DD 格式，只有年份时填 "YYYY-01-01"
6. 塔筒构造: 仔细阅读是否有"混塔""钢混塔""混合塔筒""混凝土塔筒"(hybrid)或"钢塔""全钢塔筒"(steel)的明确描述
7. 项目状态: 从上下文判断项目当前所处阶段

原文:
{content}"""


# ══════════════════════════════════════════════════════════
# 提取结果
# ══════════════════════════════════════════════════════════

@dataclass
class ExtractedProject:
    """LLM 提取的项目结构化数据"""
    has_project: bool = False
    project_name: str | None = None
    province: str | None = None
    project_type: str | None = None          # "onshore" | "offshore"
    capacity_mw: float | None = None
    turbine_count: int | None = None
    unit_capacity_mw: float | None = None
    tower_type: str | None = None            # "steel" | "hybrid"
    status: str | None = None
    owner: str | None = None
    turbine_supplier: str | None = None
    investment_bn: float | None = None
    approval_date: str | None = None
    bid_date: str | None = None
    construction_start_date: str | None = None
    completion_date: str | None = None
    planned_cod_date: str | None = None

    # 元数据
    extraction_confidence: float = 0.0
    raw_llm_response: dict = field(default_factory=dict)


# ══════════════════════════════════════════════════════════
# 提取器
# ══════════════════════════════════════════════════════════

class LLMExtractor:
    """
    使用 Claude API 从新闻文本中提取风电项目结构化信息
    使用 Haiku 模型（成本低、速度快，适合批量提取）
    """

    MODEL = "claude-haiku-4-5"

    def __init__(self, api_key: str | None = None):
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self._cache: dict[str, ExtractedProject] = {}   # 内容 hash → 提取结果

    async def extract(self, content: str, title: str = "") -> ExtractedProject:
        """从文章内容提取项目信息（带缓存）"""
        import hashlib
        content_hash = hashlib.md5(content[:2000].encode()).hexdigest()

        if content_hash in self._cache:
            logger.debug(f"Cache hit for content hash={content_hash[:8]}")
            return self._cache[content_hash]

        result = await self._call_claude(content, title)
        self._cache[content_hash] = result
        return result

    async def _call_claude(self, content: str, title: str) -> ExtractedProject:
        """调用 Claude API 提取"""
        # 限制输入长度（Haiku 上下文 200K，但我们限制成本）
        text = f"标题: {title}\n\n{content}" if title else content
        if len(text) > 8000:
            text = text[:8000]

        prompt = EXTRACT_PROMPT.format(content=text)

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=1024,
                temperature=0.0,          # 确定性输出
                system="你是一个风电行业数据分析助手。从新闻/公告中精确提取风电项目结构化信息。",
                messages=[{"role": "user", "content": prompt}],
                tools=[EXTRACT_PROJECT_TOOL],
            )

            return self._parse_response(response)

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return ExtractedProject(has_project=False)

    def _parse_response(self, response) -> ExtractedProject:
        """解析 Claude 的 Tool Use 响应"""
        for block in response.content:
            if block.type == "tool_use" and block.name == "extract_wind_project":
                data = block.input
                return ExtractedProject(
                    has_project=data.get("has_project", False),
                    project_name=data.get("project_name"),
                    province=data.get("province"),
                    project_type=data.get("project_type"),
                    capacity_mw=data.get("capacity_mw"),
                    turbine_count=data.get("turbine_count"),
                    unit_capacity_mw=data.get("unit_capacity_mw"),
                    tower_type=data.get("tower_type"),
                    status=data.get("status"),
                    owner=data.get("owner"),
                    turbine_supplier=data.get("turbine_supplier"),
                    investment_bn=data.get("investment_bn"),
                    approval_date=data.get("approval_date"),
                    bid_date=data.get("bid_date"),
                    construction_start_date=data.get("construction_start_date"),
                    completion_date=data.get("completion_date"),
                    planned_cod_date=data.get("planned_cod_date"),
                    extraction_confidence=0.9,
                    raw_llm_response=data,
                )

        # 没有 tool_use，尝试从 content 文本解析（fallback）
        for block in response.content:
            if block.type == "text" and block.text:
                logger.warning(f"No tool_use in response, raw text: {block.text[:200]}")
                break

        return ExtractedProject(has_project=False)
