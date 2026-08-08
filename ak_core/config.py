"""可选配置文件加载：让 config.json 真实生效（零额外依赖）。

优先级：环境变量 > config.json > 内置默认值。
- 文件路径：`AK_CONFIG` 环境变量，默认取当前目录下的 `config.json`
- 什么都不配置也能跑——一切走默认。示例见仓库 `config.example.json`
- 库使用者不想读文件时，直接给 ArkCore 传显式参数即可，本模块不会自动加载

支持的键（均可省略）：
  data_dir: str                数据目录（默认 AK_DATA_DIR 或 ~/arknights-data）
  user_data_dir: str           用户数据目录（默认 <data_dir>/userdata）
  daily_pull_limit: int        每日抽卡上限，0 = 无限
  starting_jade: int           新用户初始合成玉
  crawler_interval_seconds: float  爬虫请求最小间隔（限速，秒）
"""
from __future__ import annotations

import json
import os

DEFAULTS: dict = {
    "data_dir": None,
    "user_data_dir": None,
    "daily_pull_limit": 0,
    "starting_jade": 60000,
    "crawler_interval_seconds": 1.5,
}


def _config_path() -> str:
    return os.environ.get("AK_CONFIG", "config.json")


def load_config(path: str | None = None) -> dict:
    """读取配置。找不到/损坏都返回默认值，绝不抛异常。"""
    cfg = dict(DEFAULTS)
    p = path or _config_path()
    if p and os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
        except Exception as e:
            print(f"[warn] 配置文件读取失败 {p}: {e}")
    return cfg


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default
