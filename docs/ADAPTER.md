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

## 接入 LangBot / Kirara-AI / NoobBot / ChatGPT-on-WeChat 等

这些框架没有现成适配器，但都一样简单——**跑一个 HTTP 服务，然后在框架的消息处理里
发起一次 HTTP 请求**（任何能发请求的语言/框架都行）：

```bash
ark-tools server --port 8900   # 先启动 HTTP 服务
```

```python
# 在你自己的框架插件里，把用户消息转发给它
import requests
r = requests.post("http://127.0.0.1:8900/chat",
                  json={"user_id": "123", "text": "十连"}).json()
reply_text = r["data"]["text"]     # 直接拿文本发出去
avatar = r["data"].get("image")    # 有头像就发图片
```

不同框架的接入点：

| 框架 | 在哪调 HTTP | 参考 |
|------|------------|------|
| LangBot | 自定义工具 / 插件事件回调 | 任意 Python 插件里 `requests.post` 即可 |
| Kirara-AI | 插件 / 事件监听 | 同上 |
| NoobBot | 插件 / 事件处理 | 同上 |
| ChatGPT-on-WeChat | 插件 `on_event` 回调 | 同上 |

如果你想要某个框架的"放进去就能用"适配器，按下方「加新框架 = 复制一个壳」，
把上面的 HTTP 调用换成 `handler.handle()` 直接调用即可。

## 加新框架 = 复制一个壳

1. 复制 `adapters/astrbot/main.py` 的 `_reply` 模式
2. 把你的框架的「命令/消息事件」映射到 `handler.handle()`
3. 把返回 dict 发出去

**核心逻辑、命令、数据——一行都不用改。**
