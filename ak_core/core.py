"""ArkCore：明日方舟数据系统的框架无关核心门面。

任何 bot 框架（AstrBot/NoneBot2/Koishi/ZeroBot…）都可以：
  1. 实例化 ArkCore()（数据目录取 AK_DATA_DIR 或默认 ~/arknights-data）
  2. 把聊天命令翻译成对 core 的调用
  3. 把返回的 dict/str 拼成自己的消息格式发出去

本模块不依赖任何框架。
"""
from __future__ import annotations

import json
import random
import re
from datetime import date
from pathlib import Path

from .data import DataStore, default_data_dir
from .gacha import GachaEngine, _up_names


class ArkCore:
    def __init__(self, data_dir: str | None = None, user_data_dir: str | None = None):
        data_dir = data_dir or default_data_dir()
        self.store = DataStore(data_dir)
        self.engine = GachaEngine(self.store)
        self.user_dir = Path(user_data_dir or str(Path(data_dir) / "userdata"))
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self._users: dict[str, dict] = {}
        self.daily_limit = 0  # 每日上限：0 = 无限（游戏本身无硬上限）

    # ---------- 用户数据 ----------

    def _user(self, user_id: str) -> dict:
        if user_id not in self._users:
            path = self.user_dir / f"{user_id}.json"
            if path.exists():
                try:
                    self._users[user_id] = json.loads(path.read_text(encoding="utf-8"))
                    return self._users[user_id]
                except Exception:
                    pass
            self._users[user_id] = {
                "currencies": {"jade": 60000, "originium": 0, "blue_ticket": 0},
                "pity": {}, "pool_pulls": {}, "banner_state": {},
                "owned": {}, "history": [], "total_pulls": 0,
                "day": str(date.today()), "daily": 0,
                "daily_free": {"date": "", "used": []},
                "bn": "标准寻访", "recruit": {"permits": 3, "lmd": 20000, "in_progress": [], "history": []},
            }
        u = self._users[user_id]
        if u.get("day") != str(date.today()):
            u["day"] = str(date.today())
            u["daily"] = 0
        return u

    def _save(self, user_id: str):
        try:
            (self.user_dir / f"{user_id}.json").write_text(
                json.dumps(self._users[user_id], ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass

    # ---------- 卡池 ----------

    def list_banners(self) -> list[dict]:
        return self.store.banners or []

    def get_banner(self, name: str) -> dict:
        for b in self.store.banners:
            if b["name"] == name:
                return b
        return {"banner_id": "standard_default", "name": "标准寻访", "type": "standard",
                "rate_up_6": [], "rate_up_5": []}

    def current_banner(self, user_id: str) -> dict:
        u = self._user(user_id)
        return self.get_banner(u.get("bn", "标准寻访"))

    def switch_banner(self, user_id: str, target: str) -> bool:
        for b in self.store.banners:
            if target == b["name"] or target in b["name"]:
                self._user(user_id)["bn"] = b["name"]
                self._save(user_id)
                return True
        return False

    # ---------- 抽卡 ----------

    def pull(self, user_id: str, banner_name: str | None = None, count: int = 1) -> dict:
        u = self._user(user_id)
        b = self.get_banner(banner_name or u.get("bn", "标准寻访"))
        if self.daily_limit > 0 and u["daily"] + count > self.daily_limit:
            return {"ok": False, "error": f"今日抽卡已达上限({self.daily_limit}抽)，明天再来吧~"}
        cost = (count // 10) * 6000 + (count % 10) * 600
        if u["currencies"].get("jade", 0) < cost:
            return {"ok": False, "error": f"合成玉不足（需 {cost}，现有 {u['currencies'].get('jade', 0)}）"}
        u["currencies"]["jade"] -= cost
        u["daily"] += count
        results = self.engine.roll_batch(u, b, count)
        for r in results:
            owned = u["owned"].setdefault(r["key"] or r["name"], {"copies": 0})
            owned["copies"] += 1
            u["history"].append({
                "ts": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
                "name": r["name"], "star": r["star"], "bn": b["name"],
            })
        u["history"] = u["history"][-200:]
        st = u["pity"].get(self.engine.pity_group(b), {"p6": 0})
        bst = u["banner_state"].get(b.get("banner_id", ""), {})
        self._save(user_id)
        return {
            "ok": True, "banner": b["name"], "results": results,
            "p6": st["p6"], "soft_start": self.store.soft_pity.get("start", 51),
            "spark_pulls": bst.get("spark_pulls", 0),
            "jade": u["currencies"].get("jade", 0),
            "total_pulls": u["total_pulls"],
        }

    def pity_info(self, user_id: str) -> dict:
        u = self._user(user_id)
        groups = {}
        for gid, st in u.get("pity", {}).items():
            groups[gid] = {"p6": st.get("p6", 0), "p5": st.get("p5", 0)}
        return {"banner": u.get("bn", "标准寻访"), "total_pulls": u.get("total_pulls", 0),
                "pity_groups": groups, "soft_start": self.store.soft_pity.get("start", 51)}

    def spark(self, user_id: str) -> dict:
        u = self._user(user_id)
        b = self.current_banner(user_id)
        if b.get("type") != "limited":
            return {"ok": False, "error": "只有限定池才能井哦~"}
        bst = u["banner_state"].setdefault(b["banner_id"], {
            "select_pulls": 0, "spark_pulls": 0, "collab_progress": 0, "exchanged_300": False})
        if bst.get("exchanged_300"):
            return {"ok": False, "error": "这个池子的限定已经井过了哦~"}
        if bst.get("spark_pulls", 0) < 300:
            return {"ok": False, "error": f"井进度 {bst.get('spark_pulls', 0)}/300"}
        limited = [uo["name"] for uo in b.get("rate_up_6", []) if isinstance(uo, dict) and uo.get("limited")]
        target = limited[0] if limited else (list(_up_names(b, 6))[0] if _up_names(b, 6) else "???")
        bst["exchanged_300"] = True
        bst["spark_pulls"] = 0
        owned = u["owned"].setdefault(target, {"copies": 0})
        owned["copies"] += 1
        self._save(user_id)
        return {"ok": True, "name": target}

    def free_pull(self, user_id: str) -> dict:
        u = self._user(user_id)
        b = self.current_banner(user_id)
        if not b.get("free_pull", {}).get("enabled"):
            return {"ok": False, "error": "当前卡池没有每日免费抽哦~"}
        today = str(date.today())
        df = u["daily_free"]
        if df.get("date") != today:
            u["daily_free"] = {"date": today, "used": []}
            df = u["daily_free"]
        if b["banner_id"] in df.get("used", []):
            return {"ok": False, "error": "今天的免费抽用过了哦~"}
        r = self.engine.roll_one(u, b)
        owned = u["owned"].setdefault(r["key"] or r["name"], {"copies": 0})
        owned["copies"] += 1
        df["used"].append(b["banner_id"])
        self._save(user_id)
        return {"ok": True, "result": r}

    def resources(self, user_id: str, topup: bool = False) -> dict:
        u = self._user(user_id)
        if topup:
            u["currencies"]["jade"] = max(u["currencies"].get("jade", 0), 60000)
            u["currencies"]["originium"] = u["currencies"].get("originium", 0) + 10
            self._save(user_id)
        return u["currencies"]

    # ---------- 干员查询 ----------

    def find_operator(self, keyword: str) -> dict | None:
        return self.store.find_operator(keyword)

    def operator_card(self, name: str) -> dict | None:
        op = self.store.find_operator(name)
        if not op:
            return None
        return {
            "name_zh": op["name_zh"], "name_en": op.get("name_en", ""),
            "star": op["star"], "profession": op.get("profession", ""),
            "subprofession": op.get("subprofession", ""), "position": op.get("position", ""),
            "nation": op.get("nation", ""), "race": op.get("race", ""),
            "tags": op.get("tags", []), "obtain": op.get("obtain_method", []),
            "key": op.get("key", op["name_zh"]),
            "avatar": str(self.store.avatar_path(op.get("key", op["name_zh"]))) if self.store.avatar_path(op.get("key", op["name_zh"])) else None,
        }

    def get_archive(self, name: str) -> dict | None:
        op = self.store.find_operator(name)
        if not op:
            return None
        arch = self.store.load(f"archives/{op.get('key', op['name_zh'])}.json")
        return arch or None

    def get_voice(self, name: str) -> dict | None:
        op = self.store.find_operator(name)
        if not op:
            return None
        vd = self.store.load(f"voices/{op.get('key', op['name_zh'])}.json")
        return vd or None

    def get_story(self, keyword: str) -> dict | None:
        story_dir = self.store.dir / "stories"
        if not story_dir.exists():
            return None
        for sub in ("main", "event", "operator"):
            for f in sorted((story_dir / sub).glob("*.json")):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                    if keyword in d.get("stage", ""):
                        return {"stage": d["stage"], "lines": d.get("lines", [])}
                except Exception:
                    continue
        return None

    # ---------- 公开招募 ----------

    def recruit(self, user_id: str, tags_str: str = "") -> dict:
        u = self._user(user_id)
        pool = self.store.load("recruit/recruit_pool.json") or []
        tag_map = self.store.load("recruit/recruit_tags.json") or {}
        if not pool:
            return {"ok": False, "error": "公招数据未就绪，请先同步"}
        if not tags_str.strip():
            common = [t for t in tag_map if t not in ("资深干员", "高级资深干员")]
            sel = random.sample(common, min(4, len(common)))
            roll = random.random()
            if roll < 0.03:
                sel[0] = "高级资深干员"
            elif roll < 0.2:
                sel[0] = "资深干员"
            random.shuffle(sel)
            return {"ok": True, "suggest": sel}
        chosen = [t.strip() for t in re.split(r"[\s,、]+", tags_str.strip()) if t.strip()]
        floor = 6 if "高级资深干员" in chosen else (5 if "资深干员" in chosen else 3)
        cands = None
        for t in chosen:
            names = set(tag_map.get(t, []))
            cands = names if cands is None else (cands & names)
        if not cands:
            return {"ok": False, "error": "这组标签没有对应干员哦~"}
        eligible = [op for op in pool if op["name_zh"] in cands and op["star"] >= floor] or \
                   [op for op in pool if op["name_zh"] in cands]
        if not eligible:
            return {"ok": False, "error": "没有符合条件的结果…"}
        op = random.choice(eligible)
        u["recruit"]["history"] = u["recruit"].get("history", [])[-30:]
        u["recruit"]["history"].append({"name": op["name_zh"], "star": op["star"], "tags": chosen})
        self._save(user_id)
        return {"ok": True, "operator": op, "tags": chosen}
