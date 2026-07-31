"""PRTS Wiki 共享爬取客户端。

- 描述性 UA（无 UA / 浏览器 UA 会被 WAF 403）
- 限速 1.5s/请求
- 失败指数退避重试（5 次）
- wikitext 响应缓存（断点续爬幂等）
- robots 合规：只 GET /api.php 与 /w/，不碰 /index.php、/w/Special:
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from . import get_cache_dir

import requests

API_URL = "https://prts.wiki/api.php"
USER_AGENT = "ArknightsToolkit/1.0 (PRTS wiki data fetcher; github.com/xianyu686/bot-ark-tools)"


class PrtsClient:
    def __init__(self, cache_dir: str | None = None, min_interval: float = 1.5):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.min_interval = min_interval
        self._last = 0.0
        self.cache_dir = Path(cache_dir or get_cache_dir())
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ---- 网络 ----

    def _throttle(self):
        gap = self.min_interval - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)
        self._last = time.monotonic()

    def _get(self, url: str, params: dict | None = None, timeout: int = 20):
        for attempt in range(5):
            try:
                self._throttle()
                r = self.s.get(url, params=params, timeout=timeout)
                if r.status_code == 200:
                    return r
            except requests.RequestException:
                pass
            time.sleep(2 ** attempt)
        return None

    # ---- MediaWiki API ----

    def api(self, action: str, **params) -> list[dict]:
        """调用 api.php，自动跟随 continue 游标，返回响应列表。"""
        out = []
        params = dict(params, action=action, format="json")
        while True:
            r = self._get(API_URL, params)
            if r is None:
                break
            data = r.json()
            out.append(data)
            if "continue" not in data:
                break
            params.update(data["continue"])
        return out

    # ---- 页面 wikitext（带缓存） ----

    def page_wikitext(self, title: str, refresh: bool = False) -> str | None:
        """获取页面 wikitext。命中缓存直接返回（幂等）。"""
        key = hashlib.md5(title.encode("utf-8")).hexdigest()
        cache_path = self.cache_dir / f"{key}.json"
        if not refresh and cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding="utf-8")).get("wikitext")
            except Exception:
                pass
        resp = self.api("parse", page=title, prop="wikitext", formatversion="2")
        wikitext = None
        for d in resp:
            parse = d.get("parse") or {}
            wt = parse.get("wikitext")
            if wt:
                wikitext = wt
                break
        if wikitext is not None:
            cache_path.write_text(
                json.dumps({"title": title, "wikitext": wikitext}, ensure_ascii=False),
                encoding="utf-8",
            )
        return wikitext

    # ---- Cargo ----

    def cargo(self, tables: str, fields: str, where: str = "", limit: int = 500) -> list[dict]:
        """全量拉取 Cargo 查询（limit+offset 分页）。"""
        out = []
        offset = 0
        while True:
            params = {
                "action": "cargoquery",
                "tables": tables,
                "fields": fields,
                "limit": limit,
                "format": "json",
            }
            if where:
                params["where"] = where
            params["offset"] = offset
            r = self._get(API_URL, params)
            if r is None:
                break
            data = r.json()
            items = data.get("cargoquery", [])
            if not items:
                break
            out.extend(item.get("title", {}) for item in items)
            if len(items) < limit:
                break
            offset += len(items)
        return out
