"""ark-tools 命令行：纯净包入口（零依赖任何 bot 框架）。

用法：
  ark-tools sync operators        # 同步干员数据
  ark-tools sync all              # 同步全部
  ark-tools pull --user 1 --count 10
  ark-tools operator 能天使
  ark-tools archive 能天使
  ark-tools voice 能天使
  ark-tools story 0-10
  ark-tools recruit --tags "减速 特种"
  ark-tools server --port 8899    # 启动 HTTP 微服务
"""
from __future__ import annotations

import argparse
import json
import sys

from ak_core import ArkCore, default_data_dir
from ak_core.config import load_config

CORE = None


def _core() -> ArkCore:
    """按配置（config.json / 环境变量）构建核心。显式参数优先。"""
    global CORE
    if CORE is None:
        cfg = load_config()
        CORE = ArkCore(
            data_dir=cfg.get("data_dir"),
            user_data_dir=cfg.get("user_data_dir"),
            daily_limit=cfg.get("daily_pull_limit"),
            starting_jade=cfg.get("starting_jade"),
        )
    return CORE


def _p(uid: str, banner: str, count: int):
    r = _core().pull(uid, banner or None, count)
    print(json.dumps(r, ensure_ascii=False, indent=1))


def _op(name: str):
    card = _core().operator_card(name)
    print(json.dumps(card, ensure_ascii=False, indent=1) if card else "未找到")


def _archive(name: str):
    a = _core().get_archive(name)
    print(json.dumps(a, ensure_ascii=False, indent=1) if a else "未找到")


def _voice(name: str):
    v = _core().get_voice(name)
    print(json.dumps(v, ensure_ascii=False, indent=1) if v else "未找到")


def _story(kw: str):
    s = _core().get_story(kw)
    print(json.dumps(s, ensure_ascii=False, indent=1) if s else "未找到")


def _recruit(tags: str):
    r = _core().recruit("cli", tags)
    print(json.dumps(r, ensure_ascii=False, indent=1))


def _sync(module: str):
    import subprocess
    py = sys.executable
    r = subprocess.run([py, "-m", "akdata_crawler.run", module], cwd=None)
    sys.exit(r.returncode)


def _server(port: int):
    from .server import run_server
    run_server(port=port)


def _chat(user_id: str, text: str):
    from .commands import CommandHandler
    r = CommandHandler().handle(user_id, text)
    print(r.get("text", ""))
    for seg in r.get("segments") or []:
        print(seg)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="ark-tools", description="明日方舟数据系统（纯净包）")
    ap.add_argument("--data-dir", default=None, help=f"数据目录（默认 AK_DATA_DIR 或 {default_data_dir()}）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sync", help="同步数据（operators/avatars/archives/voices/stories/recruit/banners/all）")

    p = sub.add_parser("pull", help="抽卡")
    p.add_argument("--user", required=True); p.add_argument("--banner", default=""); p.add_argument("--count", type=int, default=1)

    for name in ("operator", "archive", "voice"):
        q = sub.add_parser(name, help=f"查询{name}")
        q.add_argument("name")

    s = sub.add_parser("story", help="查剧情")
    s.add_argument("keyword")

    r = sub.add_parser("recruit", help="公招")
    r.add_argument("--tags", default="")

    sv = sub.add_parser("server", help="启动 HTTP 微服务")
    sv.add_argument("--port", type=int, default=8899)

    ch = sub.add_parser("chat", help="统一命令入口：ark-tools chat '十连'")
    ch.add_argument("--user", default="cli")
    ch.add_argument("text")

    args = ap.parse_args()

    if args.data_dir:
        import os
        os.environ["AK_DATA_DIR"] = args.data_dir

    if args.cmd == "sync":
        module = sys.argv[2] if len(sys.argv) > 2 else "all"
        _sync(module)
    elif args.cmd == "pull":
        _p(args.user, args.banner, args.count)
    elif args.cmd == "operator":
        _op(args.name)
    elif args.cmd == "archive":
        _archive(args.name)
    elif args.cmd == "voice":
        _voice(args.name)
    elif args.cmd == "story":
        _story(args.keyword)
    elif args.cmd == "recruit":
        _recruit(args.tags)
    elif args.cmd == "server":
        _server(args.port)
    elif args.cmd == "chat":
        _chat(args.user, args.text)


if __name__ == "__main__":
    main()
