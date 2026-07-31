"""抽卡引擎概率/保底正确性验证。

跑法: 用 AstrBot venv python:
  ".../astrbot/Scripts/python.exe" D:/QQBot/akdata_crawler/tests/test_prob.py
"""
import sys, random
sys.path.insert(0, r"D:/QQBot/astrbot/data/plugins/astrbot_plugin_ark_gacha")
sys.stdout.reconfigure(encoding="utf-8")

from main import DataStore, GachaEngine

store = DataStore()
engine = GachaEngine(store)
assert store.ready(), "operators.json 未加载！先跑 fetch_operators"

def fresh_user(bn="标准寻访"):
    return {
        "currencies": {"jade": 10**9},
        "pity": {}, "pool_pulls": {}, "banner_state": {},
        "owned": {}, "history": [], "total_pulls": 0,
        "bn": bn, "daily_free": {"date": "", "used": []},
    }

def banner(name):
    for b in store.banners:
        if b["name"] == name:
            return b
    return store.banners[0]

def test_basic_rates(n=200000):
    """无保底（每50次重置p6）抽样：应接近 2/8/50/40%。"""
    u = fresh_user()
    b = banner("标准寻访")
    st = u["pity"].setdefault("standard", {"p6": 0, "p5": 0})
    counts = {6: 0, 5: 0, 4: 0, 3: 0}
    for _ in range(n):
        if st["p6"] >= 50:
            st["p6"] = 0  # 模拟重置，测基础概率
        r = engine.roll_one(u, b)
        counts[r["star"]] = counts.get(r["star"], 0) + 1
    total = sum(counts.values())
    print(f"基础概率(样本{n}): " + " ".join(f"{s}★={c/total*100:.2f}%" for s, c in sorted(counts.items(), reverse=True)))

def test_soft_pity():
    """模拟带软保底抽到6★的抽取数：平均应≈34.6抽。"""
    pulls = []
    for _ in range(2000):
        u = fresh_user()
        b = banner("标准寻访")
        cnt = 0
        while True:
            r = engine.roll_one(u, b)
            cnt += 1
            if r["star"] == 6:
                break
            if cnt > 120:
                break
        pulls.append(cnt)
    avg = sum(pulls) / len(pulls)
    print(f"软保底: 平均 {avg:.2f} 抽出6★ (理论≈34.6), P50={sorted(pulls)[len(pulls)//2]}, max={max(pulls)}")

def test_ten_pull_guarantee():
    """新池前10抽必出5★+。"""
    ok = 0
    for _ in range(2000):
        u = fresh_user()
        b = banner("标准寻访")
        r = engine.roll_batch(u, b, 10)
        if any(x["star"] >= 5 for x in r):
            ok += 1
    print(f"十连保底: {ok}/2000 前10抽内必出5★+ = {ok/2000*100:.2f}% (应=100%)")

def test_limited_weights():
    """限定池：双UP各≈35%。"""
    u = fresh_user("限定寻访·盛夏")
    b = banner("限定寻访·盛夏")
    six = []
    for _ in range(5000):
        u2 = fresh_user("限定寻访·盛夏")
        while True:
            r = engine.roll_one(u2, b)
            if r["star"] == 6:
                six.append(r["name"]); break
    from collections import Counter
    c = Counter(six)
    ups = ["纯烬艾雅法拉", "佩佩"]
    print(f"限定双UP: 纯烬艾雅法拉={c.get('纯烬艾雅法拉',0)/len(six)*100:.1f}% 佩佩={c.get('佩佩',0)/len(six)*100:.1f}% (应各≈35%) 其他={sum(v for k,v in c.items() if k not in ups)/len(six)*100:.1f}%")

def test_spark():
    """300抽井进度。"""
    u = fresh_user("限定寻访·盛夏")
    b = banner("限定寻访·盛夏")
    for _ in range(30):
        engine.roll_batch(u, b, 10)
    bst = u["banner_state"][b["banner_id"]]
    print(f"井: 300抽后 spark_pulls={bst['spark_pulls']} (应=300)")

if __name__ == "__main__":
    test_basic_rates()
    test_soft_pity()
    test_ten_pull_guarantee()
    test_limited_weights()
    test_spark()
    print("\n✅ 引擎测试完成")
