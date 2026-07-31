#!/usr/bin/env python3
"""AstrBot 适配器：把聊天命令翻译成 ak_core 调用，再格式化回复。

这是「薄壳」——所有逻辑都在 ak_core 里，本文件只做 命令映射 + 消息格式。
数据版权归鹰角网络，数据由 akdata_crawler 从 PRTS Wiki 生成。
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 使 ak_core 可导入

from astrbot.api import AstrBotConfig, logger  # noqa: E402
from astrbot.api.event import AstrMessageEvent, filter  # noqa: E402
from astrbot.api.star import Context, Star, register  # noqa: E402
from astrbot.core.star.filter.command import GreedyStr  # noqa: E402

from ak_core import ArkCore, default_data_dir  # noqa: E402


@register("astrbot_plugin_ark_toolkit", "阿米娅", "明日方舟数据系统（ak_core 适配）", "1.0.0")
class ArkToolkit(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}
        data_dir = (getattr(self.config, "get", lambda k, d: d)("data_dir", "") or "") or default_data_dir()
        self.core = ArkCore(data_dir=data_dir, user_data_dir=str(Path(data_dir) / "userdata"))
        logger.info(f"明日方舟数据系统已初始化 | 数据: {data_dir}")

    # ---- 工具 ----

    def _ready(self) -> bool:
        return self.core.store.ready()

    async def _send_long(self, event, title: str, text: str, chunk: int = 1500):
        text = text or ""
        await event.send(event.plain_result(f"{title}\n\n{text[:chunk]}"))
        for i in range(chunk, len(text), chunk):
            await event.send(event.plain_result(text[i:i + chunk]))
            await asyncio.sleep(0.3)

    # ---- 菜单 ----

    @filter.command("方舟", alias={"方舟菜单", "方舟功能"})
    async def ark_menu(self, event: AstrMessageEvent):
        uid = event.get_sender_id()
        b = self.core.current_banner(uid)
        await event.send(event.plain_result(
            f"🐰 明日方舟数据系统\n当前卡池：{b['name']}\n\n"
            "🎰 寻访抽卡\n  寻访/抽卡·十连/单抽·卡池/切换 X\n"
            "  保底详情·井·免费抽·资源 充值\n\n"
            "📇 干员图鉴\n  干员 X·档案 X·语音 X·剧情 X\n\n"
            "🎯 公开招募\n  公招 标签1 标签2·公招记录\n\n"
            "🔄 资源同步\n  同步 干员/档案/语音/剧情/卡池/公招/全部"))

    # ---- 抽卡 ----

    @filter.command("寻访", alias={"抽卡"})
    async def gacha_menu(self, event: AstrMessageEvent):
        if not self._ready():
            await event.send(event.plain_result("数据未就绪，请先同步（发送「方舟」看帮助）~"))
            return
        uid = event.get_sender_id()
        b = self.core.current_banner(uid)
        await event.send(event.plain_result(
            f"🐰 罗德岛寻访中心\n当前卡池：{b['name']}\n\n"
            "发送「十连」/「单抽」/「卡池」/「保底详情」/「方舟」~"))

    async def _do_pull(self, event, count: int):
        uid = event.get_sender_id()
        r = self.core.pull(uid, None, count)
        if not r["ok"]:
            await event.send(event.plain_result(f"🐰 {r['error']}"))
            return
        lines = [f"🐰 {r['banner']} {'十连' if count > 1 else '单抽'}寻访", ""]
        for i, res in enumerate(r["results"], 1):
            tag = "  NEW!" if res["star"] >= 5 else ""
            lines.append(f"  {i:2d}. [{res['star']}★] {res['profession']} {res['name']}{tag}")
        counts = {}
        for res in r["results"]:
            counts[res["star"]] = counts.get(res["star"], 0) + 1
        ss = "  ".join(f"{s}★×{c}" for s, c in sorted(counts.items(), reverse=True))
        parts = [f"💎 6★保底 {r['p6']}/{r['soft_start']}"]
        if r["spark_pulls"]:
            parts.append(f"🌸 井 {r['spark_pulls']}/300")
        parts.append(f"📦 {ss} | 玉 {r['jade']}")
        lines.append(" | ".join(parts))
        lines.append(f"💬 累计 {r['total_pulls']} 抽")
        await event.send(event.plain_result("\n".join(lines)))

    @filter.command("十连", alias={"10连"})
    async def ten_pull(self, event: AstrMessageEvent):
        await self._do_pull(event, 10)

    @filter.command("单抽")
    async def single_pull(self, event: AstrMessageEvent):
        await self._do_pull(event, 1)

    @filter.command("卡池", alias={"卡池列表", "卡池切换", "切换"})
    async def banner_list(self, event: AstrMessageEvent):
        if not self._ready():
            await event.send(event.plain_result("数据未就绪~"))
            return
        uid = event.get_sender_id()
        msg = event.message_str.strip()
        for kw in ["切换 ", "切 "]:
            if kw in msg:
                target = msg.split(kw, 1)[1].strip()
                if self.core.switch_banner(uid, target):
                    await event.send(event.plain_result(f"🐰 已切换至「{self.core.current_banner(uid)['name']}」~"))
                else:
                    await event.send(event.plain_result(f"没找到「{target}」这个卡池哦~"))
                return
        b = self.core.current_banner(uid)
        tag = {"limited": "🌸", "newbie": "🌟", "zhongjian": "🔵", "standard": "⭐", "collab": "🎮"}
        lines = [f"🐰 当前卡池：{b['name']}", ""]
        for x in self.core.list_banners():
            lines.append(f"  {tag.get(x['type'], '⭐')} {x['name']}")
        lines += ["", "发送「切换 卡池190」切换~", "🌟 数据来源 PRTS Wiki"]
        await event.send(event.plain_result("\n".join(lines)))

    @filter.command("保底", alias={"保底详情", "寻访记录"})
    async def pity(self, event: AstrMessageEvent):
        uid = event.get_sender_id()
        info = self.core.pity_info(uid)
        lines = [f"🌟 {info['banner']} | 累计 {info['total_pulls']} 抽", ""]
        for gid, st in info["pity_groups"].items():
            label = gid.split(":")[0]
            lines.append(f"  {label}: 6★ {st['p6']}/{info['soft_start']} | 5★ {st['p5']}/9")
        await event.send(event.plain_result("\n".join(lines) or "暂无记录"))

    @filter.command("井", alias={"兑换"})
    async def spark(self, event: AstrMessageEvent):
        r = self.core.spark(event.get_sender_id())
        await event.send(event.plain_result(
            f"🌸 300 抽达成，兑换到限定 6★ **{r['name']}**！" if r["ok"] else f"🐰 {r['error']}"))

    @filter.command("免费抽", alias={"每日免费"})
    async def free_pull(self, event: AstrMessageEvent):
        r = self.core.free_pull(event.get_sender_id())
        if r["ok"]:
            res = r["result"]
            await event.send(event.plain_result(f"🎁 免费抽！[{res['star']}★] {res['profession']} {res['name']}"))
        else:
            await event.send(event.plain_result(f"🐰 {r['error']}"))

    @filter.command("资源")
    async def resources(self, event: AstrMessageEvent):
        topup = "充值" in event.message_str or "充" in event.message_str
        c = self.core.resources(event.get_sender_id(), topup=topup)
        await event.send(event.plain_result(
            f"💎 合成玉：{c.get('jade', 0)} | 💠 源石：{c.get('originium', 0)}"
            + ("（已充值到 6w）" if topup else "\n发送「资源 充值」补充~")))

    # ---- 干员查询 ----

    @filter.command("干员", alias={"干员图鉴", "图鉴"})
    async def operator_card(self, event: AstrMessageEvent, name: GreedyStr = ""):
        card = self.core.operator_card(name or "")
        if not card:
            await event.send(event.plain_result("阿米娅没找到这位干员哦~"))
            return
        lines = [f"📇 {card['name_zh']} ({card['name_en']})",
                 f"⭐ {card['star']}★ | {card['profession']}/{card['subprofession']}",
                 f"📍 {card['position']} | 🌍 {card['nation']} | 🧬 {card['race']}",
                 f"🏷 {'/'.join(card['tags'])}"]
        if card["avatar"]:
            await event.send(event.make_result().message("\n".join(lines)).file_image(card["avatar"]))
        else:
            await event.send(event.plain_result("\n".join(lines)))

    @filter.command("档案", alias={"干员档案"})
    async def operator_archive(self, event: AstrMessageEvent, name: GreedyStr = ""):
        arch = self.core.get_archive(name or "")
        if not arch:
            await event.send(event.plain_result("没找到这位干员或档案未就绪~"))
            return
        op = self.core.find_operator(name or "")
        body = "\n\n".join(f"【{k}】\n{v}" for k, v in arch.items() if k != "name_zh")
        await self._send_long(event, f"📜 {op['name_zh'] if op else ''} 干员档案", body)

    @filter.command("语音", alias={"台词"})
    async def operator_voice(self, event: AstrMessageEvent, name: GreedyStr = ""):
        vd = self.core.get_voice(name or "")
        if not vd or not vd.get("lines"):
            await event.send(event.plain_result("没找到这位干员或语音未就绪~"))
            return
        op = self.core.find_operator(name or "")
        body = "\n".join(f"【{l.get('title', '')}】{l.get('zh', '')}" for l in vd["lines"])
        await self._send_long(event, f"🎤 {op['name_zh'] if op else ''} 语音记录", body)

    @filter.command("剧情", alias={"看剧情"})
    async def story(self, event: AstrMessageEvent, name: GreedyStr = ""):
        d = self.core.get_story(name or "")
        if not d:
            await event.send(event.plain_result("没找到相关剧情哦~"))
            return
        body_lines = []
        for ln in d["lines"]:
            if ln.get("type") == "dialogue":
                body_lines.append(f"{ln.get('speaker', '')}: {ln.get('text', '')}")
            elif ln.get("type") == "text":
                body_lines.append(ln.get("text", ""))
        await self._send_long(event, f"📖 {d['stage']}", "\n".join(body_lines))

    # ---- 公招 ----

    @filter.command("公招", alias={"招募"})
    async def recruit(self, event: AstrMessageEvent, tags: GreedyStr = ""):
        r = self.core.recruit(event.get_sender_id(), tags or "")
        if r["ok"] and r.get("suggest"):
            await event.send(event.plain_result(
                "🎯 公开招募标签：\n  " + " / ".join(r["suggest"]) +
                "\n\n发送「公招 标签1 标签2」选择组合（资深保5★，高资保6★）~"))
        elif r["ok"]:
            op = r["operator"]
            await event.send(event.plain_result(
                f"🎯 公招结果：[{op['star']}★] {op['profession']} {op['name_zh']}\n标签：{'/'.join(r['tags'])}"))
        else:
            await event.send(event.plain_result(f"🐰 {r['error']}"))

    @filter.command("公招记录", alias={"招募记录"})
    async def recruit_history(self, event: AstrMessageEvent):
        uid = event.get_sender_id()
        hist = self.core._user(uid)["recruit"].get("history", [])
        if not hist:
            await event.send(event.plain_result("还没有公招记录哦~"))
            return
        lines = ["🎯 最近公招："]
        for h in hist[-10:]:
            lines.append(f"  [{h['star']}★] {h['name']} ({'/'.join(h.get('tags', []))})")
        await event.send(event.plain_result("\n".join(lines)))
