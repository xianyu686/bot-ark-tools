"""PRTS「干员一览」页面 HTML 解析器。

干员记录是压缩单行的 <div data-zh="..." data-xxx="..." ...> 元素，
用 re.findall 提取全部 423 条，再逐属性解析。
"""
from __future__ import annotations

import re

# data-zh 开头到 > 结束（含全部 data-* 属性），不跨块
_DIV_RE = re.compile(r'<div (data-zh="[^"]*"[^>]*?)>')

_ATTR_RE = re.compile(r'data-([a-z_]+)="([^"]*)"')

# 0基稀有度 → 星级
RARITY_TO_STAR = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6}


def parse_operators_html(html: str) -> list[dict]:
    """解析干员一览 HTML，返回干员 dict 列表。"""
    ops = []
    for m in _DIV_RE.finditer(html):
        attrs = dict(_ATTR_RE.findall(m.group(1)))
        zh = attrs.get("zh", "").strip()
        if not zh:
            continue
        rarity = attrs.get("rarity", "")
        try:
            star = RARITY_TO_STAR.get(int(rarity), 0)
        except ValueError:
            star = 0
        op = {
            "name_zh": zh,
            "name_en": attrs.get("en", ""),
            "name_ja": attrs.get("ja", ""),
            "char_id": attrs.get("id", ""),
            "star": star,
            "profession": attrs.get("profession", ""),
            "subprofession": attrs.get("subprofession", ""),
            "position": attrs.get("position", ""),
            "nation": attrs.get("nation", ""),
            "race": attrs.get("race", ""),
            "team": attrs.get("team", ""),
            "birth_place": attrs.get("birth_place", ""),
            "logo": attrs.get("logo", ""),
            "sex": attrs.get("sex", ""),
            "tags": [t for t in attrs.get("tag", "").split() if t],
            "obtain_method": [t.strip() for t in attrs.get("obtain_method", "").split(",") if t.strip()],
            "stats": {
                "hp": attrs.get("hp", ""), "atk": attrs.get("atk", ""),
                "def": attrs.get("def", ""), "res": attrs.get("res", ""),
                "cost": attrs.get("cost", ""), "block": attrs.get("block", ""),
                "interval": attrs.get("interval", ""), "re_deploy": attrs.get("re_deploy", ""),
            },
            "sortid": attrs.get("sortid", ""),
        }
        ops.append(op)
    return ops


def build_index(ops: list[dict]) -> dict:
    """构造查询索引：中文/英文/日文/char_id → key(中文名)。"""
    index: dict[str, str] = {}
    for op in ops:
        zh = op["name_zh"]
        index.setdefault(zh.lower(), zh)
        for k in ("name_en", "name_ja", "char_id"):
            v = op.get(k, "")
            if v:
                index.setdefault(v.lower(), zh)
    return index
