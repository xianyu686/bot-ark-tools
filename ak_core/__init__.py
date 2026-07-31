"""明日方舟数据系统 - 纯净核心引擎（零依赖任何 bot 框架）。

用法：
    from ak_core import ArkCore
    core = ArkCore()
    result = core.pull("user_id", "标准轮换·卡池190", 10)

配 CLI/HTTP 服务：ark-tools sync | pull | server（见 ak_tools）
"""
from .data import DataStore, default_data_dir
from .gacha import GachaEngine
from .core import ArkCore

__all__ = ["ArkCore", "DataStore", "GachaEngine", "default_data_dir"]
__version__ = "1.0.0"
