"""抓取/解析干员全量数据 → D:/AKData/operators.json + operator_index.json。

用法：
  python -m akdata_crawler.fetch_operators [--live] [--refresh]
  --live    从 PRTS 实时抓取「干员一览」页面（默认读本地快照 D:\QQBot\prts_operators.html）
  --refresh 强制重新生成（默认：operators.json 已存在且非空则跳过）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .parsers.operators_html import parse_operators_html, build_index

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path("D:/AKData")
SNAPSHOT = Path("D:/QQBot/prts_operators.html")
LIVE_URL = "https://prts.wiki/w/干员一览"


def main(live: bool = False, refresh: bool = False):
    ops_path = DATA_DIR / "operators.json"
    if not refresh and ops_path.exists() and ops_path.stat().st_size > 0:
        print(f"[skip] {ops_path} 已存在")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if live:
        from .prts_client import PrtsClient
        client = PrtsClient()
        r = client._get(LIVE_URL)
        if r is None:
            print("[warn] 实时抓取失败，回退本地快照")
            html = SNAPSHOT.read_text(encoding="utf-8")
        else:
            html = r.text
    else:
        if not SNAPSHOT.exists():
            print(f"[err] 本地快照不存在: {SNAPSHOT}，请用 --live")
            sys.exit(1)
        html = SNAPSHOT.read_text(encoding="utf-8")

    ops = parse_operators_html(html)
    if not ops:
        print("[err] 未解析到任何干员")
        sys.exit(1)

    # 去重：按中文名去重（阿米娅(近卫) 等异格单独保留，但同名真干员只取一条）
    seen = {}
    for op in ops:
        seen.setdefault(op["name_zh"], op)
    ops = list(seen.values())

    # key 用中文名（查卡池/档案最直观），char_id 保留
    for op in ops:
        op["key"] = op["name_zh"]

    ops.sort(key=lambda o: o.get("sortid", "") or "")
    index = build_index(ops)

    ops_path.write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "operator_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (DATA_DIR / "meta").mkdir(exist_ok=True)
    (DATA_DIR / "meta" / "manifest.json").write_text(
        json.dumps({"operators_fetched_at": __import__("datetime").datetime.now().isoformat(),
                    "count": len(ops)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stars = {}
    for op in ops:
        stars[op["star"]] = stars.get(op["star"], 0) + 1
    print(f"[OK] 干员 {len(ops)} 名写入 {ops_path}")
    print(f"     星级分布: {dict(sorted(stars.items()))}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    main(live=args.live, refresh=args.refresh)
