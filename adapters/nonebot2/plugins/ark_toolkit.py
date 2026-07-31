"""NoneBot2 适配器示例：把聊天命令翻译成 ak_core 调用。

这证明核心引擎「框架无关」——逻辑全在 ak_core，这里只是薄壳。

安装：
  pip install nonebot2 nonebot-adapter-onebot
  # 把本文件放入 NoneBot2 的 plugins/ 目录
"""
from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment

from ak_core import ArkCore

core = ArkCore()  # 数据目录可用环境变量 AK_DATA_DIR 配置


def fmt_pull(r: dict) -> str:
    lines = [f"🐰 {r['banner']}  {'十连' if len(r['results']) > 1 else '单抽'}寻访", ""]
    for i, res in enumerate(r["results"], 1):
        lines.append(f"  {i:2d}. [{res['star']}★] {res['profession']} {res['name']}")
    return "\n".join(lines)


# ---------- 抽卡 ----------

@on_command("十连", aliases={"10连"}).handle()
async def ten_pull(event: MessageEvent):
    r = core.pull(event.get_user_id(), None, 10)
    await event.finish(fmt_pull(r))


@on_command("单抽").handle()
async def single_pull(event: MessageEvent):
    r = core.pull(event.get_user_id(), None, 1)
    await event.finish(fmt_pull(r))


@on_command("卡池", aliases={"卡池列表"}).handle()
async def banner_list(event: MessageEvent):
    b = core.current_banner(event.get_user_id())
    lines = [f"🐰 当前卡池：{b['name']}", ""]
    for x in core.list_banners():
        lines.append(f"  {x['name']}")
    lines.append("")
    lines.append("发送「切换 <卡池名>」切换~")
    await event.finish("\n".join(lines))


@on_command("切换").handle()
async def switch_banner(event: MessageEvent):
    target = str(event.message).strip().replace("切换", "").strip()
    if core.switch_banner(event.get_user_id(), target):
        await event.finish(f"🐰 已切换至「{core.current_banner(event.get_user_id())['name']}」~")
    await event.finish(f"没找到「{target}」这个卡池哦~")


# ---------- 干员查询 ----------

@on_command("干员").handle()
async def operator_card(event: MessageEvent):
    name = str(event.message).strip().replace("干员", "").strip()
    card = core.operator_card(name)
    if not card:
        await event.finish("没找到这位干员哦~")
    msg = (f"📇 {card['name_zh']} ({card['name_en']})\n"
           f"⭐ {card['star']}★ | {card['profession']}/{card['subprofession']}\n"
           f"📍 {card['position']} | 🌍 {card['nation']} | 🧬 {card['race']}")
    if card.get("avatar"):
        await event.send(MessageSegment.image(f"file:///{card['avatar']}"))
    await event.finish(msg)


@on_command("档案").handle()
async def archive(event: MessageEvent):
    name = str(event.message).strip().replace("档案", "").strip()
    arch = core.get_archive(name)
    if not arch:
        await event.finish("没找到这位干员或档案未就绪~")
    body = "\n\n".join(f"【{k}】\n{v}" for k, v in arch.items() if k != "name_zh")
    await event.finish(body)


@on_command("剧情").handle()
async def story(event: MessageEvent):
    kw = str(event.message).strip().replace("剧情", "").strip()
    d = core.get_story(kw)
    if not d:
        await event.finish("没找到相关剧情哦~")
    body = "\n".join(
        (f"{ln.get('speaker', '')}: {ln.get('text', '')}" if ln.get("type") == "dialogue"
         else ln.get("text", ""))
        for ln in d["lines"])
    await event.finish(f"📖 {d['stage']}\n{body}")


# ---------- 公招 ----------

@on_command("公招").handle()
async def recruit(event: MessageEvent):
    tags = str(event.message).strip().replace("公招", "").strip()
    r = core.recruit(event.get_user_id(), tags)
    if r["ok"] and r.get("suggest"):
        await event.finish("🎯 随机标签：\n  " + " / ".join(r["suggest"]) +
                           "\n\n发送「公招 标签1 标签2」选择组合~")
    elif r["ok"]:
        op = r["operator"]
        await event.finish(f"🎯 公招结果：[{op['star']}★] {op['profession']} {op['name_zh']}")
    else:
        await event.finish(f"🐰 {r['error']}")
