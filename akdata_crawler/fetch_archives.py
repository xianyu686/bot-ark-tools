"""抓取干员档案 → D:\\AKData\\archives\\<key>.json。

用法: python -m akdata_crawler.fetch_archives [--refresh] [--limit N]
断点续爬：已完成的干员跳过，失败重试后记录 failed。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .prts_client import PrtsClient

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path("D:/AKData")
ARCHIVE_DIR = DATA_DIR / "archives"
FETCH_LOG = DATA_DIR / "meta" / "fetch_log.json"

_TITLE_RE = re.compile(r"\|档案(\d+)=([^\n|]*)")
_TEXT_RE = re.compile(r"\|档案(\d+)文本=(.*?)(?=\n\|档案\d+=|\n\}\}|\Z)", re.S)

_SECTION_LABEL = {
    "基础档案": "基础档案", "综合体检测试": "综合体检测试",
    "客观履历": "客观履历", "临床诊断分析": "临床诊断分析",
    "档案资料一": "档案资料一", "档案资料二": "档案资料二",
    "档案资料三": "档案资料三", "档案资料四": "档案资料四",
    "晋升记录": "晋升记录",
}


def parse_archive(wikitext: str) -> dict:
    """从干员页 wikitext 提取档案字段（档案N=标题 / 档案N文本=内容）。"""
    titles = {int(m.group(1)): m.group(2).strip()
              for m in _TITLE_RE.finditer(wikitext)}
    result = {}
    for m in _TEXT_RE.finditer(wikitext):
        idx = int(m.group(1))
        text = m.group(2).strip()
        if not text:
            continue
        text = re.sub(r"\{\{[^}]*\}\}", "", text).strip()
        if text:
            result[titles.get(idx, f"档案{idx}")] = text
    return result


def load_log() -> dict:
    if FETCH_LOG.exists():
        try:
            return json.loads(FETCH_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"archives": {"done": [], "failed": []}}


def save_log(log: dict):
    FETCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    FETCH_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")


def main(refresh: bool = False, limit: int = 0):
    ops_path = DATA_DIR / "operators.json"
    if not ops_path.exists():
        print("[err] 先跑 fetch_operators")
        sys.exit(1)
    ops = json.loads(ops_path.read_text(encoding="utf-8"))
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    log = load_log()
    log.setdefault("archives", {"done": [], "failed": []})
    done = set(log.get("archives", {}).get("done", []))
    client = PrtsClient()

    todo = []
    for op in ops:
        key = op.get("key") or op["name_zh"]
        if refresh or key not in done:
            todo.append((key, op["name_zh"]))
    if limit:
        todo = todo[:limit]
    print(f"[go] 待抓档案 {len(todo)} 名")

    ok = 0
    fail = 0
    for i, (key, name) in enumerate(todo, 1):
        wt = client.page_wikitext(name)
        if wt is None:
            fail += 1
            log["archives"]["failed"] = list(set(log["archives"].get("failed", []) + [key]))
            continue
        archive = parse_archive(wt)
        (ARCHIVE_DIR / f"{key}.json").write_text(
            json.dumps({"name_zh": name, **archive}, ensure_ascii=False, indent=1), encoding="utf-8")
        done.add(key)
        ok += 1
        if i % 25 == 0 or i == len(todo):
            log["archives"]["done"] = sorted(done)
            save_log(log)
            print(f"  进度 {i}/{len(todo)}")
    log["archives"]["done"] = sorted(done)
    save_log(log)
    print(f"[OK] 档案 {ok} 名，失败 {fail} 名")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    main(refresh=args.refresh, limit=args.limit)
