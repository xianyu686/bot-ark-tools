"""数据层：读取 D:\\AKData 素材库（干员/卡池/档案/语音/剧情/公招）。

数据由用户运行 akdata_crawler 生成，本模块只读，框架无关。
"""
from __future__ import annotations

import json
from pathlib import Path


class DataStore:
    """惰性加载 + mtime 缓存刷新。"""

    def __init__(self, data_dir: str = "D:/AKData"):
        self.dir = Path(data_dir)
        self._cache: dict[str, object] = {}
        self._mtime: dict[str, float] = {}

    def _load(self, rel: str):
        p = self.dir / rel
        if not p.exists():
            return None
        try:
            mtime = p.stat().st_mtime
            if rel in self._cache and self._mtime.get(rel) == mtime:
                return self._cache[rel]
            data = json.loads(p.read_text(encoding="utf-8"))
            self._cache[rel] = data
            self._mtime[rel] = mtime
            return data
        except Exception:
            return self._cache.get(rel)

    @property
    def operators(self) -> list[dict]:
        return self._load("operators.json") or []

    @property
    def index(self) -> dict:
        return self._load("operator_index.json") or {}

    @property
    def rules(self) -> dict:
        return self._load("gacha_rules.json") or {}

    @property
    def banners(self) -> list[dict]:
        return self._load("banners/banners.json") or []

    @property
    def base_rates(self) -> dict:
        return (self.rules.get("base_rates") or {"6": 0.02, "5": 0.08, "4": 0.50, "3": 0.40})

    @property
    def soft_pity(self) -> dict:
        return (self.rules.get("soft_pity")
                or {"start": 51, "increment_per_pull": 0.02, "cap_pull": 99, "cap_rate": 1.0})

    def ready(self) -> bool:
        return bool(self.operators)

    def load(self, rel: str):
        return self._load(rel)

    def avatar_path(self, key: str) -> Path | None:
        p = self.dir / "avatars" / f"{key}.png"
        return p if p.exists() else None

    def find_operator(self, keyword: str) -> dict | None:
        """按中文/英文/别名模糊查干员。"""
        kw = (keyword or "").strip().lower()
        if not kw:
            return None
        key = self.index.get(kw)
        if key:
            for op in self.operators:
                if op["name_zh"] == key:
                    return op
        for op in self.operators:
            if kw in op["name_zh"].lower():
                return op
            if kw in op.get("name_en", "").lower():
                return op
        return None
