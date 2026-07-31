"""生成公开招募数据 → D:\\AKData\\recruit\\recruit_pool.json / recruit_tags.json。

用法: python -m akdata_crawler.fetch_recruit
从 operators.json 派生：obtain 含「公开招募」的干员 + 各自的公招标签(站位/职业/特性)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import get_data_dir

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = get_data_dir()
RECRUIT_DIR = DATA_DIR / "recruit"

# 公招可出现的特性标签（从 data-tag 过滤）
RECRUIT_TAGS = {
    "输出", "生存", "防护", "治疗", "支援", "减速", "位移", "控场",
    "爆发", "快速复活", "召唤", "削弱", "新手", "资深干员", "高级资深干员",
}
# 职业标签（公招里 职业 也算 tag，实际用"近战位/远程位"+职业名）
PROFESSION_TAGS = {"先锋", "近卫", "重装", "狙击", "术师", "医疗", "辅助", "特种"}


def main():
    ops_path = DATA_DIR / "operators.json"
    if not ops_path.exists():
        print("[err] 先跑 fetch_operators")
        sys.exit(1)
    ops = json.loads(ops_path.read_text(encoding="utf-8"))
    RECRUIT_DIR.mkdir(parents=True, exist_ok=True)

    pool = []
    for op in ops:
        obtain = op.get("obtain_method") or []
        if "公开招募" not in obtain:
            continue
        key = op.get("key") or op["name_zh"]
        tags = set()
        pos = op.get("position", "")
        if pos == "近战位":
            tags.add("近战位")
        elif pos == "远程位":
            tags.add("远程位")
        prof = op.get("profession", "")
        if prof in PROFESSION_TAGS:
            tags.add(prof)
        for t in op.get("tags", []):
            if t in RECRUIT_TAGS:
                tags.add(t)
        # 2★/3★ 常见特性补全（PRTS 公招标签）
        if op["star"] >= 4:
            tags.add("资深干员")
        if op["star"] == 6:
            tags.add("高级资深干员")
        pool.append({
            "key": key, "name_zh": op["name_zh"], "star": op["star"],
            "profession": prof, "position": pos, "tags": sorted(tags),
        })

    # tag → 干员
    tag_map = {}
    for op in pool:
        for t in op["tags"]:
            tag_map.setdefault(t, []).append(op["name_zh"])

    RECRUIT_DIR.mkdir(exist_ok=True)
    (RECRUIT_DIR / "recruit_pool.json").write_text(
        json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    (RECRUIT_DIR / "recruit_tags.json").write_text(
        json.dumps(tag_map, ensure_ascii=False, indent=1), encoding="utf-8")

    stars = {}
    for op in pool:
        stars[op["star"]] = stars.get(op["star"], 0) + 1
    print(f"[OK] 公招池 {len(pool)} 名干员，星级分布 {dict(sorted(stars.items()))}")
    print(f"     标签 {len(tag_map)} 种")


if __name__ == "__main__":
    main()
