"""NoneBot2 适配器（超薄壳）：消息文本 → CommandHandler → 发回复。

安装：pip install nonebot2 nonebot-adapter-onebot
把本文件放入 NoneBot2 的 plugins/ 目录。

注意：NoneBot2 的 on_command 触发后，event.message 只含命令名之后的参数（不含命令名本身）。
所以这里每个命令都要把「命令词 + 参数」拼回完整文本再交给 CommandHandler 分发。
"""
from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment

from ak_tools.commands import CommandHandler

handler = CommandHandler()


async def _reply(event: MessageEvent, text: str):
    """把完整命令文本交给 CommandHandler，然后按序发回文本/分段/图片。

    注意用 event.send 而非 event.finish：finish 发完正文会中止后续分段/图片。
    """
    r = handler.handle(event.get_user_id(), text)
    if r["text"]:
        await event.send(r["text"])
    for seg in (r.get("segments") or []):
        await event.send(seg)
    if r.get("image"):
        await event.send(MessageSegment.image(f"file:///{r['image']}"))


def _args(event: MessageEvent) -> str:
    """命令后的参数（on_command 的 event.message 不含命令名）。"""
    return str(event.message).strip()


@on_command("方舟", aliases={"方舟菜单", "菜单", "功能"}).handle()
async def ark_menu(event: MessageEvent):
    await _reply(event, "方舟")


@on_command("十连", aliases={"10连"}).handle()
async def ten_pull(event: MessageEvent):
    await _reply(event, "十连")


@on_command("单抽").handle()
async def single_pull(event: MessageEvent):
    await _reply(event, "单抽")


@on_command("卡池", aliases={"卡池列表", "卡池切换", "切换"}).handle()
async def banner(event: MessageEvent):
    await _reply(event, f"卡池 {_args(event)}".strip())


@on_command("保底", aliases={"保底详情", "寻访记录"}).handle()
async def pity(event: MessageEvent):
    await _reply(event, "保底详情")


@on_command("井", aliases={"兑换"}).handle()
async def spark(event: MessageEvent):
    await _reply(event, "井")


@on_command("免费抽", aliases={"每日免费"}).handle()
async def free_pull(event: MessageEvent):
    await _reply(event, "免费抽")


@on_command("资源").handle()
async def resources(event: MessageEvent):
    await _reply(event, f"资源 {_args(event)}".strip())


@on_command("干员", aliases={"干员图鉴", "图鉴"}).handle()
async def operator_card(event: MessageEvent):
    await _reply(event, f"干员 {_args(event)}".strip())


@on_command("档案", aliases={"干员档案"}).handle()
async def operator_archive(event: MessageEvent):
    await _reply(event, f"档案 {_args(event)}".strip())


@on_command("语音", aliases={"台词"}).handle()
async def operator_voice(event: MessageEvent):
    await _reply(event, f"语音 {_args(event)}".strip())


@on_command("剧情", aliases={"看剧情"}).handle()
async def story(event: MessageEvent):
    await _reply(event, f"剧情 {_args(event)}".strip())


@on_command("公招", aliases={"招募"}).handle()
async def recruit(event: MessageEvent):
    await _reply(event, f"公招 {_args(event)}".strip())


@on_command("公招记录", aliases={"招募记录"}).handle()
async def recruit_history(event: MessageEvent):
    await _reply(event, "公招记录")
