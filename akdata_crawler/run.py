"""明日方舟数据爬取 CLI。

用法（在项目根目录下）：
  python -m akdata_crawler.run operators          # 干员全量（自动实时抓取）
  python -m akdata_crawler.run avatars            # 头像批量下载
  python -m akdata_crawler.run archives           # 干员档案
  python -m akdata_crawler.run voices             # 语音文本
  python -m akdata_crawler.run recruit            # 公招数据
  python -m akdata_crawler.run banners            # 卡池配置(待实现)
  python -m akdata_crawler.run stories --only main --resume   # 剧情(长任务)
  python -m akdata_crawler.run all                # 依次跑 operators/avatars/archives/voices/recruit
"""
from __future__ import annotations

import sys


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "operators":
        from .fetch_operators import main as m
        m(live="--live" in args, refresh="--refresh" in args)
    elif cmd == "avatars":
        from .fetch_avatars import main as m
        m(refresh="--refresh" in args)
    elif cmd == "archives":
        from .fetch_archives import main as m
        m(refresh="--refresh" in args, limit=_int_arg(args, "--limit"))
    elif cmd == "voices":
        from .fetch_voices import main as m
        m(limit=_int_arg(args, "--limit"))
    elif cmd == "recruit":
        from .fetch_recruit import main as m
        m()
    elif cmd == "banners":
        from .fetch_banners import main as m
        m()
    elif cmd == "stories":
        from .fetch_stories import main as m
        m(only=_str_arg(args, "--only"), resume="--resume" in args)
    elif cmd == "all":
        from .fetch_operators import main as mo
        from .fetch_avatars import main as ma
        from .fetch_archives import main as mar
        from .fetch_voices import main as mv
        from .fetch_recruit import main as mr
        print("== operators =="); mo()
        print("== avatars =="); ma()
        print("== archives =="); mar()
        print("== voices =="); mv()
        print("== recruit =="); mr()
    else:
        print(f"未知模块: {cmd}")
        print(__doc__)
        sys.exit(1)


def _int_arg(args, name, default=0):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            try:
                return int(args[i + 1])
            except ValueError:
                pass
    return default


def _str_arg(args, name, default=""):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default


if __name__ == "__main__":
    main()
