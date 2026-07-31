"""统一命令分发器：任何框架/CLI/HTTP 接入的薄壳标准。

用法：适配器拿到用户消息文本，调 handler.handle(user_id, text)，
     返回统一结构 {text, image, segments}，自己拼成框架消息即可。
"""
from __future__ import annotations

import re

from ak_core import ArkCore


class CommandHandler:
    """把「聊天文本命令」翻译成 ArkCore 调用 + 格式化回复。"""

    def __init__(self, core: ArkCore | None = None):
        self.core = core or ArkCore()

    # ---------- 命令分发 ----------

    def handle(self, user_id: str, text: str) -> dict:
        text = (text or "").strip()
        cmd, arg = self._split(text)
        if not cmd:
            return self._menu()

        if cmd in ("十连", "10连"):
            return self._pull(user_id, 10)
        if cmd in ("单抽", "抽"):
            return self._pull(user_id, 1)
        if cmd in ("卡池", "卡池列表"):
            return self._banners(user_id, arg)
        if cmd in ("切换", "切"):
            return self._switch(user_id, arg)
        if cmd in ("保底", "保底详情", "寻访记录"):
            return self._pity(user_id)
        if cmd in ("井", "兑换"):
            return self._spark(user_id)
        if cmd in ("免费抽", "每日免费"):
            return self._free(user_id)
        if cmd in ("资源", "充值"):
            return self._resources(user_id, "充值" in cmd or "充" in text)
        if cmd in ("干员", "图鉴"):
            return self._operator(arg)
        if cmd in ("档案", "干员档案"):
            return self._archive(arg)
        if cmd in ("语音", "台词"):
            return self._voice(arg)
        if cmd in ("剧情", "看剧情"):
            return self._story(arg)
        if cmd in ("公招", "招募"):
            return self._recruit(user_id, arg)
        if cmd in ("公招记录", "招募记录"):
            return self._recruit_history(user_id)
        if cmd in ("菜单", "方舟", "功能"):
            return self._menu()

        # 未匹配：可能是「干员 X」等带参命令的缺省
        if arg and not cmd:
            return self._operator(arg)
        return {"text": "没看懂哦~ 发送「方舟」查看菜单", "image": None, "segments": None}

    @staticmethod
    def _split(text: str) -> tuple[str, str]:
        """把消息切成 (命令, 参数)。支持「干员 能天使」「干员能天使」。"""
        text = text.strip()
        # 先匹配已知命令词
        known = ["十连", "10连", "单抽", "卡池", "卡池列表", "切换", "切", "保底详情", "保底",
                 "寻访记录", "井", "兑换", "免费抽", "每日免费", "资源", "充值", "干员",
                 "图鉴", "档案", "语音", "台词", "剧情", "看剧情", "公招", "招募",
                 "公招记录", "招募记录", "菜单", "方舟", "功能"]
        for kw in sorted(known, key=len, reverse=True):
            if text == kw:
                return kw, ""
            if text.startswith(kw + " ") or text.startswith(kw + "，") or text.startswith(kw + ","):
                return kw, text[len(kw):].lstrip(" ，,、")
        return text.split(maxsplit=1) if text else ("", "")

    # ---------- 各命令实现 ----------

    def _menu(self) -> dict:
        return {
            "text": (
                "🐰 明日方舟数据系统\n"
                "🎰 抽卡：十连 / 单抽 / 卡池 / 切换 X / 保底详情 / 井 / 免费抽 / 资源 充值\n"
                "📇 图鉴：干员 X / 档案 X / 语音 X / 剧情 X\n"
                "🎯 公招：公招 标签1 标签2 [时间] / 公招记录\n"
                "🔄 同步：同步 干员/档案/剧情/卡池/全部"),
            "image": None, "segments": None,
        }

    def _pull(self, user_id: str, count: int) -> dict:
        r = self.core.pull(user_id, None, count)
        if not r["ok"]:
            return {"text": f"🐰 {r['error']}", "image": None, "segments": None}
        lines = [f"🐰 {r['banner']} {'十连' if count > 1 else '单抽'}寻访", ""]
        for i, res in enumerate(r["results"], 1):
            lines.append(f"  {i:2d}. [{res['star']}★] {res['profession']} {res['name']}")
        counts = {}
        for res in r["results"]:
            counts[res["star"]] = counts.get(res["star"], 0) + 1
        ss = "  ".join(f"{s}★×{c}" for s, c in sorted(counts.items(), reverse=True))
        parts = [f"💎 6★保底 {r['p6']}/{r['soft_start']}"]
        if r["spark_pulls"]:
            parts.append(f"🌸 井 {r['spark_pulls']}/300")
        parts.append(f"📦 {ss} | 玉 {r['jade']}")
        lines.append(" | ".join(parts))
        return {"text": "\n".join(lines), "image": None, "segments": None}

    def _banners(self, user_id: str, arg: str) -> dict:
        if arg:
            return self._switch(user_id, arg)
        b = self.core.current_banner(user_id)
        lines = [f"🐰 当前卡池：{b['name']}", ""]
        for x in self.core.list_banners():
            lines.append(f"  {x['name']}")
        lines += ["", "发送「切换 <池名>」切换~"]
        return {"text": "\n".join(lines), "image": None, "segments": None}

    def _switch(self, user_id: str, target: str) -> dict:
        if self.core.switch_banner(user_id, target):
            return {"text": f"🐰 已切换至「{self.core.current_banner(user_id)['name']}」~",
                    "image": None, "segments": None}
        return {"text": f"没找到「{target}」这个卡池哦~", "image": None, "segments": None}

    def _pity(self, user_id: str) -> dict:
        info = self.core.pity_info(user_id)
        lines = [f"🌟 {info['banner']} | 累计 {info['total_pulls']} 抽", ""]
        for gid, st in info["pity_groups"].items():
            lines.append(f"  {gid.split(':')[0]}: 6★ {st['p6']}/{info['soft_start']} | 5★ {st['p5']}/9")
        return {"text": "\n".join(lines), "image": None, "segments": None}

    def _spark(self, user_id: str) -> dict:
        r = self.core.spark(user_id)
        return {"text": (f"🌸 300抽达成，兑换到 {r['name']}！" if r["ok"] else f"🐰 {r['error']}"),
                "image": None, "segments": None}

    def _free(self, user_id: str) -> dict:
        r = self.core.free_pull(user_id)
        if r["ok"]:
            res = r["result"]
            return {"text": f"🎁 免费抽！[{res['star']}★] {res['profession']} {res['name']}",
                    "image": None, "segments": None}
        return {"text": f"🐰 {r['error']}", "image": None, "segments": None}

    def _resources(self, user_id: str, topup: bool) -> dict:
        c = self.core.resources(user_id, topup=topup)
        return {"text": (f"💎 合成玉：{c.get('jade', 0)} | 💠 源石：{c.get('originium', 0)}"
                         + ("（已充值到6w）" if topup else "\n发送「资源 充值」补充~")),
                "image": None, "segments": None}

    def _operator(self, name: str) -> dict:
        card = self.core.operator_card(name)
        if not card:
            return {"text": "没找到这位干员哦~", "image": None, "segments": None}
        lines = [f"📇 {card['name_zh']} ({card['name_en']})",
                 f"⭐ {card['star']}★ | {card['profession']}/{card['subprofession']}",
                 f"📍 {card['position']} | 🌍 {card['nation']} | 🧬 {card['race']}",
                 f"🏷 {'/'.join(card['tags'])}"]
        return {"text": "\n".join(lines), "image": card.get("avatar"), "segments": None}

    def _archive(self, name: str) -> dict:
        arch = self.core.get_archive(name)
        if not arch:
            return {"text": "没找到这位干员或档案未就绪~", "image": None, "segments": None}
        body = "\n\n".join(f"【{k}】\n{v}" for k, v in arch.items() if k != "name_zh")
        return {"text": f"📜 {name} 干员档案", "image": None, "segments": self._chunk(body)}

    def _voice(self, name: str) -> dict:
        vd = self.core.get_voice(name)
        if not vd or not vd.get("lines"):
            return {"text": "没找到这位干员或语音未就绪~", "image": None, "segments": None}
        body = "\n".join(f"【{l.get('title', '')}】{l.get('zh', '')}" for l in vd["lines"])
        return {"text": f"🎤 {name} 语音记录", "image": None, "segments": self._chunk(body)}

    def _story(self, kw: str) -> dict:
        d = self.core.get_story(kw)
        if not d:
            return {"text": "没找到相关剧情哦~", "image": None, "segments": None}
        body = "\n".join(
            (f"{ln.get('speaker', '')}: {ln.get('text', '')}" if ln.get("type") == "dialogue"
             else ln.get("text", ""))
            for ln in d["lines"])
        return {"text": f"📖 {d['stage']}", "image": None, "segments": self._chunk(body)}

    def _recruit(self, user_id: str, tags: str) -> dict:
        # 最后一个形如「3:50」的 token 当作招募时间，其余是标签
        time = ""
        tokens = [t.strip() for t in re.split(r"[\s,、]+", tags.strip()) if t.strip()]
        if tokens and ":" in tokens[-1]:
            time = tokens.pop()
        tags_str = " ".join(tokens)
        r = self.core.recruit(user_id, tags_str, time)
        if r["ok"] and r.get("suggest"):
            return {"text": "🎯 随机标签：\n  " + " / ".join(r["suggest"]) +
                           "\n\n发送「公招 标签1 标签2 [时间]」选择组合~"
                           "\n⏱ 时间可选：0:10 / 0:50 / 1:00 / 1:20 / 2:20 / 3:50 / 7:40 / 9:00"
                           "\n（资深保5★，高资保6★）", "image": None, "segments": None}
        if r["ok"]:
            op = r["operator"]
            t = r.get("time") or "9:00"
            return {"text": f"🎯 公招结果：[{op['star']}★] {op['profession']} {op['name_zh']}（⏱ {t}）\n"
                            f"标签：{'/'.join(r.get('tags', []))}",
                    "image": None, "segments": None}
        return {"text": f"🐰 {r['error']}", "image": None, "segments": None}

    def _recruit_history(self, user_id: str) -> dict:
        hist = self.core.recruit_history(user_id)
        if not hist:
            return {"text": "还没有公招记录哦~", "image": None, "segments": None}
        lines = ["🎯 最近公招："]
        for h in hist[-10:]:
            t = h.get("time", "")
            lines.append(f"  [{h['star']}★] {h['name']} ({'/'.join(h.get('tags', []))})"
                         + (f" ⏱{t}" if t else ""))
        return {"text": "\n".join(lines), "image": None, "segments": None}

    @staticmethod
    def _chunk(text: str, size: int = 1500) -> list[str]:
        return [text[i:i + size] for i in range(0, len(text), size)]
