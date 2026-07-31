"""抽卡引擎：完全复刻明日方舟寻访机制（框架无关）。

- 基础概率 2/8/50/40；6星软保底 51 起 +2%/抽、99 必出
- 十连/前10抽 5★ 保底；限定双 UP 权重；300 井；选调 150/300；联动 120
- 保底分组：standard(跨池继承)/limited:bid(独立清零)/zhongjian/collab:bid/newbie
"""
from __future__ import annotations

import random

from .data import DataStore


def _weighted_choice(items_weights: list[tuple[dict, float]]) -> dict:
    total = sum(w for _, w in items_weights)
    if total <= 0:
        return items_weights[0][0] if items_weights else {}
    r = random.random() * total
    acc = 0.0
    for item, w in items_weights:
        acc += w
        if r <= acc:
            return item
    return items_weights[-1][0]


def _up_names(banner: dict, star: int) -> set[str]:
    key = "rate_up_6" if star == 6 else "rate_up_5"
    ups = banner.get(key, [])
    names = set()
    for u in ups:
        if isinstance(u, dict):
            names.add(u.get("name", ""))
        else:
            names.add(str(u))
    return {n for n in names if n}


class GachaEngine:
    def __init__(self, store: DataStore):
        self.store = store
        self.base = store.base_rates
        self.soft = store.soft_pity

    def pity_group(self, banner: dict) -> str:
        bt = banner.get("type", "standard")
        bid = banner.get("banner_id", banner.get("name", ""))
        if bt == "limited":
            return f"limited:{bid}"
        if bt == "collab":
            return f"collab:{bid}"
        if bt == "zhongjian":
            return "zhongjian"
        if bt == "newbie":
            return "newbie"
        return "standard"

    def star_pool(self, banner: dict, star: int) -> list[dict]:
        ops = self.store.operators
        btype = banner.get("type", "standard")
        if btype in ("joint", "orient"):
            ups = _up_names(banner, star)
            return [o for o in ops if o["name_zh"] in ups and o["star"] == star]
        obtain_key = "中坚寻访" if btype == "zhongjian" else "标准寻访"
        pool = [o for o in ops if o["star"] == star and obtain_key in (o.get("obtain_method") or [])]
        if btype in ("limited", "collab"):
            upnames = _up_names(banner, 6) if star == 6 else _up_names(banner, 5)
            for o in ops:
                if o["star"] == star and o["name_zh"] in upnames and o not in pool:
                    pool.append(o)
            if btype == "collab" and star == 6:
                cn = banner.get("collab_6star")
                if cn:
                    co = [o for o in ops if o["name_zh"] == cn]
                    if co and co[0] not in pool:
                        pool.append(co[0])
        return pool

    def roll_one(self, u: dict, banner: dict, force_5plus: bool = False, force_6: bool = False) -> dict:
        st = u["pity"].setdefault(self.pity_group(banner), {"p6": 0, "p5": 0})
        st["p6"] += 1
        st["p5"] += 1
        bid = banner.get("banner_id", banner.get("name", ""))
        u["pool_pulls"][bid] = u["pool_pulls"].get(bid, 0) + 1
        u["total_pulls"] += 1

        r6 = self.base["6"]
        if st["p6"] >= self.soft.get("start", 51):
            r6 = min(self.soft.get("cap_rate", 1.0),
                     self.base["6"] + (st["p6"] - self.soft.get("start", 51) + 1)
                     * self.soft.get("increment_per_pull", 0.02))
        r5 = (1.0 - r6) if force_5plus else self.base["5"]

        roll = random.random()
        if force_6 or roll < r6:
            st["p6"] = 0
            st["p5"] = 0
            op = self.pick_6star(banner, u)
        elif roll < r6 + r5:
            st["p5"] = 0
            op = self.pick_star(banner, 5)
        elif roll < r6 + r5 + self.base["4"]:
            op = self.pick_star(banner, 4)
        else:
            op = self.pick_star(banner, 3)
        return {"name": op.get("name_zh", "???"), "star": op.get("star", 0),
                "profession": op.get("profession", ""), "key": op.get("key", op.get("name_zh", ""))}

    def roll_batch(self, u: dict, banner: dict, count: int = 10) -> list[dict]:
        results = []
        bid = banner.get("banner_id", banner.get("name", ""))
        for _ in range(count):
            pulls = u["pool_pulls"].get(bid, 0) + 1
            st = u["pity"].get(self.pity_group(banner), {"p6": 0, "p5": 0})
            force_5plus = pulls <= 10 and st["p5"] >= 9
            force_6 = False
            if banner.get("type") == "newbie" and pulls <= 10 and st["p6"] >= 10:
                force_6 = True
            results.append(self.roll_one(u, banner, force_5plus=force_5plus, force_6=force_6))
        bst = u["banner_state"].setdefault(bid, {
            "select_pulls": 0, "spark_pulls": 0, "collab_progress": 0, "exchanged_300": False})
        bst["spark_pulls"] = bst.get("spark_pulls", 0) + count
        if banner.get("type") in ("standard", "zhongjian"):
            bst["select_pulls"] = bst.get("select_pulls", 0) + count
        if banner.get("type") == "collab":
            bst["collab_progress"] = bst.get("collab_progress", 0) + count
        return results

    def pick_6star(self, banner: dict, u: dict) -> dict:
        pool = self.star_pool(banner, 6)
        if not pool:
            return {}
        btype = banner.get("type", "standard")
        upnames = _up_names(banner, 6)

        if btype == "collab":
            bst = u["banner_state"].get(banner.get("banner_id", ""), {})
            if bst.get("collab_progress", 0) >= 120:
                cn = banner.get("collab_6star")
                if cn:
                    co = [o for o in pool if o["name_zh"] == cn]
                    if co:
                        bst["collab_progress"] = 0
                        return co[0]

        if btype in ("standard", "zhongjian") and banner.get("rate_up_6"):
            bst = u["banner_state"].get(banner.get("banner_id", ""), {})
            sp = bst.get("select_pulls", 0)
            ups = [o for o in pool if o["name_zh"] in upnames]
            if ups and sp >= 300 and not bst.get("select_300_done"):
                bst["select_300_done"] = True
                return ups[1] if len(ups) > 1 else ups[0]
            if ups and sp >= 150 and not bst.get("select_150_done"):
                bst["select_150_done"] = True
                return ups[0]

        if btype == "limited":
            up_ops = [o for o in pool if o["name_zh"] in upnames]
            filler = [o for o in pool if o["name_zh"] not in upnames]
            weights = []
            up_total = 0.35 * max(1, len(up_ops))
            per_up = up_total / max(1, len(up_ops)) if up_ops else 0
            for o in up_ops:
                weights.append((o, per_up))
            fw = (1.0 - up_total) / max(1, len(filler)) if filler else 0
            for o in filler:
                weights.append((o, fw))
            if weights:
                return _weighted_choice(weights)

        if btype in ("joint", "orient"):
            ups = [o for o in pool if o["name_zh"] in upnames]
            return random.choice(ups or pool)

        if btype == "crossyear":
            owned = set(u.get("owned", {}).keys())
            unowned = [o for o in pool if o["name_zh"] not in owned]
            if unowned:
                return random.choice(unowned)
        up_ops = [o for o in pool if o["name_zh"] in upnames]
        if up_ops and random.random() < 0.5:
            return random.choice(up_ops)
        return random.choice(pool)

    def pick_star(self, banner: dict, star: int) -> dict:
        pool = self.star_pool(banner, star)
        if not pool:
            return {}
        upnames = _up_names(banner, star)
        up_ops = [o for o in pool if o["name_zh"] in upnames]
        if up_ops and random.random() < 0.5:
            return random.choice(up_ops)
        return random.choice(pool)
