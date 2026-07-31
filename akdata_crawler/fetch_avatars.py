"""批量下载干员头像 → D:\\AKData\\avatars\\<key>.png。

用法: python -m akdata_crawler.fetch_avatars [--refresh]
幂等：已存在的头像跳过。
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path

from .prts_client import PrtsClient

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = get_data_dir()
AVATAR_DIR = DATA_DIR / "avatars"
BATCH = 50


def main(refresh: bool = False):
    ops_path = DATA_DIR / "operators.json"
    if not ops_path.exists():
        print("[err] 先跑 fetch_operators")
        sys.exit(1)
    ops = json.loads(ops_path.read_text(encoding="utf-8"))
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    # 收集缺的头像
    todo = []
    for op in ops:
        key = op.get("key") or op["name_zh"]
        img = AVATAR_DIR / f"{key}.png"
        if refresh or not img.exists():
            todo.append((key, op["name_zh"]))
    if not todo:
        print(f"[skip] 全部 {len(ops)} 个头像已存在")
        return
    print(f"[go] 需要下载 {len(todo)} 个头像")

    client = PrtsClient()
    downloaded = 0
    failed = []
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        titles = "|".join(f"File:头像 {name}.png" for _, name in batch)
        resp = client.api("query", titles=titles, prop="imageinfo",
                          iiprop="url|size", formatversion="2")
        url_map = {}
        for d in resp:
            for page in d.get("query", {}).get("pages", []):
                ii = (page.get("imageinfo") or [{}])[0]
                title = page.get("title", "")
                url = ii.get("url")
                if url:
                    # title 形如 文件:头像 XX.png（前缀可能是 File: 或 文件:）
                    name = title.replace(".png", "").rsplit("头像 ", 1)[-1]
                    url_map[name] = url
        for key, name in batch:
            url = url_map.get(name)
            if not url:
                failed.append(name)
                continue
            try:
                # media.prts.wiki 是 OSS 直链，无需节流，直接下载
                import requests
                r = requests.get(url, headers={"User-Agent": "PRTS-Wiki-Research/1.0"},
                                 timeout=30)
                if r.status_code != 200:
                    failed.append(name)
                    continue
                (AVATAR_DIR / f"{key}.png").write_bytes(r.content)
                downloaded += 1
            except Exception:
                failed.append(name)
        print(f"  进度 {min(i + BATCH, len(todo))}/{len(todo)}")

    print(f"[OK] 下载 {downloaded} 个，失败 {len(failed)}: {failed[:10]}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    main(refresh=args.refresh)
