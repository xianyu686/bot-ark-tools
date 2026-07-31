# 适配器开发指南（任何框架 5 步接入）

> 核心引擎 `ak_core` 零框架依赖；统一命令分发器 `CommandHandler` 让接入任何 bot 框架变成「喂文本 → 收回复」的薄壳。

## 原理

```
用户消息文本 → CommandHandler.handle(user_id, text) → {"text": ..., "image": ..., "segments": [...]}
                                                        ↑ 适配器只做两件事：
                                                          1. 把框架消息转成文本 + user_id
                                                          2. 把返回 dict 拼成框架消息发出去
```

`CommandHandler` 已内置全部命令（十连/单抽/卡池/切换/保底/井/免费抽/资源/干员/档案/语音/剧情/公招/方舟菜单），你**不用写任何命令逻辑**。

## 返回值结构

```python
{
  "text": "主要回复文本",
  "image": "/path/to/avatar.png 或 None",   # 可选：本地图片路径
  "segments": ["长文分段1", "分段2", ...] 或 None,  # 可选：档案/剧情等长文本分段
}
```

## 5 步接入

```python
from ak_tools.commands import CommandHandler

handler = CommandHandler()          # 1. 创建分发器

def on_message(user_id, raw_text):  # 2. 你的框架的消息处理函数
    r = handler.handle(user_id, raw_text)   # 3. 喂文本
    send(r["text"])                          # 4. 发文本
    for seg in r["segments"] or []:          # 5. 发分段/图片
        send(seg)
    if r["image"]:
        send_image(r["image"])
```

就这么多。`adapters/` 里 AstrBot 和 NoneBot2 的现成实现可直接参考。

## 现有适配器

| 框架 | 位置 | 说明 |
|------|------|------|
| AstrBot | `adapters/astrbot/` | 超薄壳：命令 → `_reply()` → handler |
| NoneBot2 | `adapters/nonebot2/plugins/ark_toolkit.py` | 超薄壳：`on_command` → `_reply()` → handler |
| HTTP 服务 | `ark-tools server` 的 `POST /chat` | 任何语言都能 `curl` 调用 |

## 加新框架 = 复制一个壳

1. 复制 `adapters/astrbot/main.py` 的 `_reply` 模式
2. 把你的框架的「命令/消息事件」映射到 `handler.handle()`
3. 把返回 dict 发出去

**核心逻辑、命令、数据——一行都不用改。**
