"""从 PRTS「卡池一览」抓取真实卡池 → D:\\AKData\\banners\\banners.json。

用法: python -m akdata_crawler.run banners [--refresh]
解析「卡池一览/限时寻访」的 wikitext 表格，输出池名/时间/UP 6★5★/限定标记。
分类：含「限定干员…仅在」→ limited；含 狩猎凯旋/联动 等 → collab；否则 → standard。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import get_data_dir

from .prts_client import PrtsClient

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = get_data_dir()
BANNER_DIR = DATA_DIR / "banners"
# 静态基础池（标准/中坚/新手，永不覆盖）
FALLBACK = "banners_base.json"


def _banner_name(cell: str) -> str:
    """从 [[文件:...jpg|400px|link=X]]<br/>[[X|显示名]] 提取显示名（跳过文件链接）。"""
    links = re.findall(r"\[\[([^\]|]*)\|([^\]]*)\]\]", cell)
    for src, disp in reversed(links):
        if not src.startswith("文件:"):
            return disp.strip() or src.strip()
    m = re.search(r"\[\[([^\]|]*)\]\]", cell)
    return m.group(1).strip() if m else cell.strip()[:30]


def _avatar_names(cell: str) -> list[dict]:
    """提取 {{干员头像|XX}} 中的干员名；若带 limited=1 标记为限定。"""
    out = []
    for m in re.finditer(r"\{\{干员头像\|([^}|]*)(?:\|[^}]*?)?\}\}", cell):
        name = m.group(1).strip()
        limited = "limited=1" in m.group(0)
        if name:
            out.append({"name": name, "limited": limited})
    return out


def _banner_type(name: str, col3: str, col4: str) -> str:
    """分类池型：collab(联动) > limited(限定) > standard。"""
    full = name + col3 + col4
    if "联动" in full or "狩猎凯旋" in full or "怪物猎人" in full:
        return "collab"
    if "限定干员" in full or "限定" in name:
        return "limited"
    return "standard"


def parse_limited_page(wikitext: str) -> list[dict]:
    """解析「卡池一览/限时寻访」表格。"""
    banners = []
    # 找表格主体（{|class="wikitable ... |}）
    tbl = re.search(r"\{\| ?class=\"wikitable.*?\n((?:.|\n)*?)\n\|\}", wikitext)
    if not tbl:
        return banners
    rows = re.split(r"\n\|-\s*\n", tbl.group(1))
    for row in rows:
        cells = [c.strip() for c in row.strip().lstrip("|").split("\n|")]
        cells = [c for c in cells if c]
        if len(cells) < 4:
            continue
        name = _banner_name(cells[0])
        if not name:
            continue
        dates = "~".join(d.strip() for d in re.findall(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", cells[1]))
        up6 = _avatar_names(cells[2])
        up5 = _avatar_names(cells[3])
        btype = _banner_type(name, cells[2], cells[3])
        banners.append({
            "banner_id": re.sub(r"[^\w\u4e00-\u9fff-]", "_", name),
            "name": name,
            "type": btype,
            "desc": name,
            "start": dates.split("~")[0] if "~" in dates else dates,
            "end": dates.split("~")[1] if "~" in dates else "",
            "rate_up_6": up6,
            "rate_up_5": [u["name"] for u in up5],
            "free_pull": {"enabled": btype == "limited"},
        })
    return banners


def parse_standard_page(wikitext: str, today: str = "") -> list[dict]:
    """解析「常驻标准寻访/YYYY」轮换表，返回当前在开的轮换池。"""
    today = today or __import__("datetime").date.today().isoformat()
    banners = []
    tbl = re.search(r"\{\| ?class=\"wikitable.*?\n((?:.|\n)*?)\n\|\}", wikitext)
    if not tbl:
        return banners
    rows = re.split(r"\n\|-\s*\n", tbl.group(1))
    for row in rows:
        cells = [c.strip() for c in row.strip().lstrip("|").split("\n|")]
        cells = [c for c in cells if c]
        if len(cells) < 5:
            continue
        num = re.search(r"\|?(\d+)", cells[0])
        num = num.group(1) if num else "?"
        dates = cells[2].replace("<br/>", " ")
        dms = re.findall(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", dates)
        if len(dms) < 2:
            continue
        start, end = dms[0], dms[1]
        # 只保留当前在开的轮换
        if not (start <= today + " 23:59" <= end):
            continue
        name = f"标准轮换·卡池{num}"
        banners.append({
            "banner_id": f"standard_{num}",
            "name": name,
            "type": "standard",
            "desc": f"常驻标准轮换·卡池{num}",
            "start": start, "end": end,
            "rate_up_6": _avatar_names(cells[3]),
            "rate_up_5": [u["name"] for u in _avatar_names(cells[4])],
            "free_pull": {"enabled": False},
        })
    return banners


def main(refresh: bool = False):
    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    client = PrtsClient()
    wt = client.page_wikitext("卡池一览/限时寻访", refresh=refresh)
    limited = parse_limited_page(wt) if wt else []
    print(f"[OK] 限时/活动池 {len(limited)} 个")

    std_wt = client.page_wikitext("卡池一览/常驻标准寻访/2026", refresh=refresh)
    std = parse_standard_page(std_wt) if std_wt else []
    print(f"[OK] 当前标准轮换 {len(std)} 个")

    fallback = json.loads((BANNER_DIR / FALLBACK).read_text(encoding="utf-8"))
    base = [b for b in fallback if b["type"] in ("standard", "zhongjian", "newbie")]

    all_banners = base + std + limited
    seen = {}
    for b in all_banners:
        seen.setdefault(b["name"], b)
    all_banners = list(seen.values())

    (BANNER_DIR / "banners.json").write_text(
        json.dumps(all_banners, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] 合并后共 {len(all_banners)} 个池 -> banners.json")
    for b in all_banners:
        ups = [u["name"] if isinstance(u, dict) else str(u) for u in b.get("rate_up_6", [])]
        print(f"  {b['type']:<8} {b['name']} [{', '.join(ups)}]")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    main(refresh=args.refresh)
