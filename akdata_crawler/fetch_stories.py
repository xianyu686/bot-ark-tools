"""抓取剧情文本 → D:\\AKData\\stories\\{main,event,operator}\\<key>.json。

用法:
  python -m akdata_crawler.run stories --only main [--resume]
  --only main|event|operator   先跑核心主线
  --resume                     跳过已完成

长任务：断点续爬，幂等（page_wikitext 有缓存）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .prts_client import PrtsClient

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path("D:/AKData")
STORY_DIR = DATA_DIR / "stories"
FETCH_LOG = DATA_DIR / "meta" / "fetch_log.json"

# 关卡内剧情：{{#invoke:IngameStory|list\n|data=...}}
_INGAME_RE = re.compile(r"\{\{#invoke:IngameStory\|.*?data=(.*?)\}\}", re.S)


def parse_ingame_story(wikitext: str) -> list[dict]:
    """解析关卡内剧情 IngameStory data。

    每行 TYPE;;field1;;field2;;...：
      C = 角色介绍（C;;名字;;头像 X;;...）
      S = 角色对白（S;;X;;头像 <名字>;;台词）
      T = 旁白/文本（T;;文本）
    """
    m = _INGAME_RE.search(wikitext)
    if not m:
        return []
    lines = []
    for raw in m.group(1).split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split(";;")
        kind = parts[0].strip()
        if kind == "S" and len(parts) >= 4:
            speaker = parts[2].replace("头像 ", "").strip()
            text = "".join(parts[3:]).strip()
            if text:
                lines.append({"type": "dialogue", "speaker": speaker, "text": text})
        elif kind == "T" and len(parts) >= 2:
            text = "".join(parts[1:]).strip()
            if text:
                lines.append({"type": "text", "text": text})
    return lines


def parse_story_simulator(wikitext: str) -> list[dict]:
    """解析干员密录的「剧情模拟器」脚本格式。

    - [指令] 行跳过；[name="X"]台词 为角色对白（可带行内文本或后续行）
    - 纯文本行为旁白，若有当前 speaker 则归为对白
    """
    lines = []
    speaker = ""
    for raw in wikitext.split("\n"):
        line = raw.strip()
        if not line:
            continue
        # 跳过模板元数据（{{剧情模拟器|...}} 头部、参数行、嵌套模板、闭合）
        if line.startswith("{{") or line.startswith("|") or line.startswith("}}"):
            continue
        if re.match(r"^[A-Za-z_]+=", line):  # 参数行 图片数据=... 音频数据=...
            continue
        if line.startswith("["):
            m = re.match(r'\[name="([^"]*)"\]\s*(.*)$', line)
            if m:
                speaker = m.group(1).strip()
                text = m.group(2).strip()
                if text:
                    lines.append({"type": "dialogue", "speaker": speaker or "???", "text": text})
            continue
        if speaker:
            lines.append({"type": "dialogue", "speaker": speaker, "text": line})
        else:
            lines.append({"type": "text", "text": line})
    return lines


def load_log() -> dict:
    if FETCH_LOG.exists():
        try:
            return json.loads(FETCH_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"stories": {"done": [], "failed": []}}


def save_log(log: dict):
    FETCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    FETCH_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")


def _enumerate_stages(client: PrtsClient, category: str) -> list[str]:
    """枚举分类下的关卡页标题。"""
    titles = []
    continue_param = None
    while True:
        params = dict(list="categorymembers", cmtitle=f"Category:{category}", cmlimit="500", formatversion="2")
        if continue_param:
            params.update(continue_param)
        resp = client.api("query", **params)
        if not resp:
            break
        data = resp[0]
        titles.extend(p["title"] for p in data.get("query", {}).get("categorymembers", []))
        if "continue" not in data:
            break
        continue_param = data["continue"]
    return titles


def main(only: str = "", resume: bool = False):
    STORY_DIR.mkdir(parents=True, exist_ok=True)
    log = load_log()
    log.setdefault("stories", {"done": [], "failed": []})
    done = set(log.get("stories", {}).get("done", []))
    client = PrtsClient()

    # 目标：主线 + 活动 + 干员密录
    targets = []
    if only in ("", "main"):
        targets.append(("main", "主线关卡"))
    if only in ("", "event"):
        targets.append(("event", "活动关卡"))
    if only in ("", "operator"):
        targets.append(("operator", "干员密录"))

    for subdir, category in targets:
        (STORY_DIR / subdir).mkdir(exist_ok=True)
        stages = _enumerate_stages(client, category)
        if not stages:
            print(f"[warn] {category} 分类枚举为空")
            continue
        print(f"[go] {category}: {len(stages)} 个页面")
        ok = fail = 0
        for i, stage in enumerate(stages, 1):
            key = re.sub(r"[^\w\u4e00-\u9fff-]", "_", stage)
            out = STORY_DIR / subdir / f"{key}.json"
            if not resume and key in done:
                continue
            wt = client.page_wikitext(stage)
            if wt is None:
                fail += 1
                continue
            lines = parse_ingame_story(wt)
            if not lines:
                lines = parse_story_simulator(wt)  # 干员密录用剧情模拟器格式
            if lines:
                out.write_text(json.dumps(
                    {"stage": stage, "lines": lines}, ensure_ascii=False, indent=1), encoding="utf-8")
                ok += 1
                done.add(key)
            else:
                # 无剧情也标记完成，避免重爬
                done.add(key)
            if i % 20 == 0 or i == len(stages):
                log["stories"]["done"] = sorted(done)
                save_log(log)
                print(f"  {category} 进度 {i}/{len(stages)}")
        print(f"[OK] {category}: 含剧情 {ok}，失败 {fail}")

    log["stories"]["done"] = sorted(done)
    save_log(log)
    print("[OK] 剧情爬取完成（当前批次）")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    main(only=args.only, resume=args.resume)
