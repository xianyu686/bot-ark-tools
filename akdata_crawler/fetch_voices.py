"""抓取干员语音文本 → D:\\AKData\\voices\\<key>.json。

用法: python -m akdata_crawler.fetch_voices [--limit N]
断点续爬，音频暂不下（URL 规则待探，先存文本）。
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
VOICE_DIR = DATA_DIR / "voices"
FETCH_LOG = DATA_DIR / "meta" / "fetch_log.json"


def parse_voice(wikitext: str) -> list[dict]:
    """解析 {{VoiceTable|...}} → [{title, trigger, zh}]。"""
    titles = {int(m.group(1)): m.group(2).strip()
              for m in re.finditer(r"\|标题(\d+)=([^|\n]*)", wikitext)}
    triggers = {int(m.group(1)): m.group(2).strip()
                for m in re.finditer(r"\|触发类型(\d+)=([^|\n]*)", wikitext)}
    zh_map = {}
    for m in re.finditer(r"\|台词(\d+)=\{\{VoiceData/word\|中文\|([^}]+)\}\}", wikitext):
        idx = int(m.group(1))
        text = " ".join(m.group(2).split())
        if text:
            zh_map[idx] = text

    return [
        {"title": titles.get(idx, ""), "trigger": triggers.get(idx, ""), "zh": zh_map[idx]}
        for idx in sorted(zh_map)
    ]


def load_log() -> dict:
    if FETCH_LOG.exists():
        try:
            return json.loads(FETCH_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"voices": {"done": [], "failed": []}}


def save_log(log: dict):
    FETCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    FETCH_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")


def main(limit: int = 0):
    ops_path = DATA_DIR / "operators.json"
    if not ops_path.exists():
        print("[err] 先跑 fetch_operators")
        sys.exit(1)
    ops = json.loads(ops_path.read_text(encoding="utf-8"))
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    log = load_log()
    log.setdefault("voices", {"done": [], "failed": []})
    done = set(log.get("voices", {}).get("done", []))
    client = PrtsClient()

    todo = [(op.get("key") or op["name_zh"], op["name_zh"]) for op in ops
            if (op.get("key") or op["name_zh"]) not in done]
    if limit:
        todo = todo[:limit]
    print(f"[go] 待抓语音 {len(todo)} 名")

    ok = fail = 0
    for i, (key, name) in enumerate(todo, 1):
        wt = client.page_wikitext(f"{name}/语音记录")
        if wt is None:
            fail += 1
            log["voices"]["failed"] = list(set(log["voices"].get("failed", []) + [key]))
            continue
        lines = parse_voice(wt)
        (VOICE_DIR / f"{key}.json").write_text(
            json.dumps({"name_zh": name, "lines": lines}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        done.add(key)
        ok += 1
        if i % 25 == 0 or i == len(todo):
            log["voices"]["done"] = sorted(done)
            save_log(log)
            print(f"  进度 {i}/{len(todo)}")
    log["voices"]["done"] = sorted(done)
    save_log(log)
    print(f"[OK] 语音 {ok} 名，失败 {fail} 名")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    main(limit=args.limit)
