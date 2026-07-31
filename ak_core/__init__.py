"""明日方舟数据系统 - 核心引擎（框架无关）。

用法：
    from ak_core import ArkCore
    core = ArkCore(data_dir="D:/AKData", user_data_dir="D:/AKData/userdata")
    result = core.pull("2337879474", "标准轮换·卡池190", 10)
"""
from .data import DataStore, default_data_dir
from .gacha import GachaEngine
from .core import ArkCore

__all__ = ["ArkCore", "DataStore", "GachaEngine", "default_data_dir"]
__version__ = "1.0.0"
