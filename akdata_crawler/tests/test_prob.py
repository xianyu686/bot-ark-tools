"""抽卡引擎概率/保底正确性验证（纯净包）。

跑法：
  python -m akdata_crawler.tests.test_prob
  # 或： python akdata_crawler/tests/test_prob.py
"""
import sys, random
sys.path.insert(0, __file__.rsplit("akdata_crawler", 1)[0])
sys.stdout.reconfigure(encoding="utf-8")

from ak_core import ArkCore

core = ArkCore()
store = core.store
engine = core.engine
assert store.ready(), "数据未加载！先跑爬虫（AK_DATA_DIR 指向数据目录）"
