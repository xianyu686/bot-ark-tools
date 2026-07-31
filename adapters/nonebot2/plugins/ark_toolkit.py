"""NoneBot2 适配器（超薄壳）：消息文本 → CommandHandler → 发回复。

安装：pip install nonebot2 nonebot-adapter-onebot
把本文件放入 NoneBot2 的 plugins/ 目录。
"""
from __future__ import annotations

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment

from ak_tools.commands import CommandHandler

handler = CommandHandler()


def _reply(event: MessageEvent, text: str):
    r = handler.handle(event.get_user_id(), text)
    # 先发文本
    if r["text"]:
        event.finish(r["text"])
    # 分段
    for seg in (r.get("segments") or []):
        event.send(seg)
    # 头像
    if r.get("image"):
        event.send(MessageSegment.image(f"file:///{r['image']}"))


# 统一命令入口：所有命令都过 CommandHandler
@on_command("方舟", aliases={"菜单", "功能"}).handle()
async def menu(event: MessageEvent):
    _reply(event, "方舟")


@on_command("十连", aliases={"10连"}).handle()
async def ten_pull(event: MessageEvent):
    _reply(event, "十连")


@on_command("单抽").handle()
async def single_pull(event: MessageEvent):
    _reply(event, "单抽")


@on_command("卡池", aliases={"卡池列表", "切换"}).handle()
async def banner(event: MessageEvent):
    _reply(event, str(event.message).strip())


@on_command("干员", aliases={"图鉴", "档案", "语音", "剧情", "公招"}).handle()
async def query(event: MessageEvent):
    _reply(event, str(event.message).strip())
