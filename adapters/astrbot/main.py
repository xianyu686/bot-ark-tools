#!/usr/bin/env python3
"""AstrBot 适配器（超薄壳）：消息文本 → CommandHandler → 发回复。

所有命令逻辑在 ak_tools.commands，这里只做事件翻译 + 消息发送。
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from astrbot.api import AstrBotConfig, logger  # noqa: E402
from astrbot.api.event import AstrMessageEvent, filter  # noqa: E402
from astrbot.api.star import Context, Star, register  # noqa: E402
from astrbot.core.star.filter.command import GreedyStr  # noqa: E402

from ak_core import default_data_dir  # noqa: E402
from ak_tools.commands import CommandHandler  # noqa: E402


@register("astrbot_plugin_ark_toolkit", "ArknightsToolkit", "明日方舟数据系统（ak_core 适配）", "1.0.0")
class ArkToolkit(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}
        self.handler = CommandHandler()
        data_dir = (getattr(self.config, "get", lambda k, d: d)("data_dir", "") or "") or default_data_dir()
        logger.info(f"明日方舟数据系统已初始化 | 数据: {data_dir}")

    async def _reply(self, event: AstrMessageEvent, text: str):
        """按「阿米娅 命令」格式去掉唤醒词后分发。"""
        msg = event.message_str.strip()
        # 去掉唤醒词（命令本身不带唤醒词）
        for kw in ("阿米娅", "bot", "助手"):
            if msg.startswith(kw + " "):
                msg = msg[len(kw):].strip()
                break
        r = self.handler.handle(event.get_sender_id(), msg)
        # 发送正文
        await event.send(event.plain_result(r["text"]))
        # 分段长文
        for seg in (r.get("segments") or []):
            await event.send(event.plain_result(seg))
            await asyncio.sleep(0.3)
        # 头像图
        if r.get("image"):
            await event.send(event.make_result().message("").file_image(r["image"]))

    @filter.command("方舟", alias={"方舟菜单", "菜单", "功能"})
    async def ark_menu(self, event: AstrMessageEvent):
        await self._reply(event, "方舟")

    @filter.command("十连", alias={"10连"})
    async def ten_pull(self, event: AstrMessageEvent):
        await self._reply(event, "十连")

    @filter.command("单抽")
    async def single_pull(self, event: AstrMessageEvent):
        await self._reply(event, "单抽")

    @filter.command("卡池", alias={"卡池列表", "卡池切换", "切换"})
    async def banner(self, event: AstrMessageEvent, arg: GreedyStr = ""):
        await self._reply(event, f"卡池 {arg}".strip() if arg else "卡池")

    @filter.command("保底", alias={"保底详情", "寻访记录"})
    async def pity(self, event: AstrMessageEvent):
        await self._reply(event, "保底详情")

    @filter.command("井", alias={"兑换"})
    async def spark(self, event: AstrMessageEvent):
        await self._reply(event, "井")

    @filter.command("免费抽", alias={"每日免费"})
    async def free_pull(self, event: AstrMessageEvent):
        await self._reply(event, "免费抽")

    @filter.command("资源")
    async def resources(self, event: AstrMessageEvent, arg: GreedyStr = ""):
        await self._reply(event, f"资源 {arg}".strip())

    @filter.command("干员", alias={"干员图鉴", "图鉴"})
    async def operator_card(self, event: AstrMessageEvent, name: GreedyStr = ""):
        await self._reply(event, f"干员 {name}".strip())

    @filter.command("档案", alias={"干员档案"})
    async def operator_archive(self, event: AstrMessageEvent, name: GreedyStr = ""):
        await self._reply(event, f"档案 {name}".strip())

    @filter.command("语音", alias={"台词"})
    async def operator_voice(self, event: AstrMessageEvent, name: GreedyStr = ""):
        await self._reply(event, f"语音 {name}".strip())

    @filter.command("剧情", alias={"看剧情"})
    async def story(self, event: AstrMessageEvent, name: GreedyStr = ""):
        await self._reply(event, f"剧情 {name}".strip())

    @filter.command("公招", alias={"招募"})
    async def recruit(self, event: AstrMessageEvent, tags: GreedyStr = ""):
        await self._reply(event, f"公招 {tags}".strip())
