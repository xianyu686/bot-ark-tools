"""akdata_crawler - PRTS Wiki 爬虫。

数据目录：环境变量 AK_DATA_DIR，默认 ~/arknights-data。
"""
from __future__ import annotations

import os
from pathlib import Path


def get_data_dir() -> Path:
    return Path(os.environ.get("AK_DATA_DIR", str(Path.home() / "arknights-data")))


def get_cache_dir() -> Path:
    return get_data_dir() / "cache" / "raw"
