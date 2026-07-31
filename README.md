<div align="center">

# Arknights Toolkit · 明日方舟数据系统

**纯净 · 框架无关 · 即插即用**

一个零依赖 bot 框架的明日方舟数据核心：完整复刻寻访机制 + 干员图鉴 / 档案 / 语音 / 剧情 / 公招。

[![PyPI](https://img.shields.io/pypi/v/arknights-datakit?color=blue)](https://pypi.org/project/arknights-datakit/)
[![Python](https://img.shields.io/pypi/pyversions/arknights-datakit)](https://pypi.org/project/arknights-datakit/)
[![License](https://img.shields.io/github/license/xianyu686/bot-ark-tools)](LICENSE)
[![Stars](https://img.shields.io/github/stars/xianyu686/bot-ark-tools?style=social)](https://github.com/xianyu686/bot-ark-tools)
[![Last Commit](https://img.shields.io/github/last-commit/xianyu686/bot-ark-tools)](https://github.com/xianyu686/bot-ark-tools)

</div>

## ✨ 什么是「纯净」？

- 🧩 **零框架依赖** — 核心引擎是纯 Python，`import ak_core` 就能用，不绑定任何 bot 框架
- 🔌 **即插即用** — 自带 `ark-tools` CLI 和 HTTP 微服务，任何框架 / 网页 / 脚本都能调
- 📦 **纯代码** — 仓库只含代码，**不含任何游戏数据 / 图片 / 密钥**
- 🔄 **数据自取** — 数据由用户运行爬虫从 PRTS 获取，实时更新

## 🚀 快速开始

```bash
pip install arknights-datakit

ark-tools sync all              # 同步全部数据（自动实时抓取）
ark-tools pull --user 1 --count 10   # 抽十连
ark-tools server --port 8900    # 启动 HTTP 微服务
```

> 数据目录默认 `~/arknights-data`，可用环境变量 `AK_DATA_DIR` 修改。

## ✨ 功能

- 🎰 **寻访抽卡** — 完全复刻游戏机制：
  - 基础概率 6★2% / 5★8% / 4★50% / 3★40%
  - 6★ 软保底（51 抽起 +2%/抽，99 抽必出）
  - 十连 / 前 10 抽 5★ 保底
  - 限定池双 UP 权重 + 300 抽井
  - 标准选调 150/300、联动 120 保底
  - 中坚寻访独立保底、跨池继承规则
- 📇 **干员图鉴** — 干员信息卡 + 头像
- 📜 **干员档案** — 完整档案（基础 / 履历 / 诊断 / 档案1-4）
- 🎤 **语音记录** — 全部台词文本
- 📖 **剧情** — 主线 / 活动 / 干员密录
- 🎯 **公开招募** — tag 组合锁定稀有度
- 🔄 **资源同步** — 从 PRTS 增量爬取，断点续爬

## 🖥️ 纯净包用法

装完自带 `ark-tools` 命令（零 bot 框架依赖）：

```bash
ark-tools sync operators|avatars|archives|voices|stories|recruit|banners|all
ark-tools pull --user <id> --banner <池名> --count 10
ark-tools operator 能天使      # 查干员
ark-tools archive 能天使       # 查档案
ark-tools voice 能天使         # 查语音
ark-tools story 0-10           # 查剧情
ark-tools recruit --tags "减速 特种"
ark-tools server --port 8900   # HTTP 微服务
```

**HTTP 微服务**（任何框架 / 网页 / 脚本都能调）：

```bash
ark-tools server --port 8900
curl http://127.0.0.1:8900/health
curl "http://127.0.0.1:8900/operator?name=%E8%83%BD%E5%A4%A9%E4%BD%BF"
curl -X POST http://127.0.0.1:8900/gacha/pull -d '{"user_id":"1","count":10}'
```

> 中文参数需 URL 编码（HTTP 标准）。接口见 [docs/API.md](docs/API.md)。

## 🏗️ 架构

```
┌────────────────────────────────────────────────┐
│  ak_core          核心引擎（纯 Python，零框架依赖）   │
│                   input: 普通参数 → output: 普通 dict │
└────────────────────────────────────────────────┘
        ▲ 调用                        ▲ 调用
┌─────────────────────┐     ┌───────────────────────────┐
│ adapters/astrbot     │     │ adapters/<任意框架>          │
│ AstrBot 适配器（薄壳） │     │ NoneBot2/Koishi/ZeroBot…    │
└─────────────────────┘     │ 每个框架一个目录，即插即用     │
                            └───────────────────────────┘
        ▲ 读数据
┌────────────────────────────────────────────────┐
│  akdata_crawler     PRTS Wiki 爬虫                │
│  生成数据目录（干员/卡池/档案/语音/剧情/公招）        │
└────────────────────────────────────────────────┘
```

**设计原则**：
- `ak_core` **零框架依赖** — 输入普通参数，返回普通 dict，任何 bot 都能调
- **适配器可插拔** — `adapters/<框架>/` 一个目录一个框架，都是「命令 → 调核心 → 拼消息」的薄壳
- 数据与代码分离 — 仓库不含数据，用户自己爬

## 🔌 接入 bot（统一命令分发器）

所有命令逻辑集中在 `CommandHandler`（`ak_tools/commands.py`）——**适配器只需「喂文本 → 收回复」**。返回值统一 `{text, image, segments}`。

**HTTP 服务**（任何框架/语言都能接）：
```bash
ark-tools server --port 8900
curl -X POST http://127.0.0.1:8900/chat -d '{"user_id":"1","text":"十连"}'
```

**AstrBot**：把 `adapters/astrbot/` 放入 `data/plugins/`，重启后：
```
[唤醒词] 方舟 · 十连 · 卡池 · 干员 X · 档案 X · 语音 X · 剧情 X · 公招
```

**NoneBot2**：把 `adapters/nonebot2/plugins/ark_toolkit.py` 放入 `plugins/`（需 `pip install nonebot2 nonebot-adapter-onebot`）。

**其他框架**：见 [docs/ADAPTER.md](docs/ADAPTER.md) —— 5 步接入，核心逻辑一行不改。

## 🔧 核心 API

```python
from ak_core import ArkCore

core = ArkCore()  # 数据目录取 AK_DATA_DIR（默认 ~/arknights-data）

core.pull("user_id", "标准轮换·卡池190", 10)   # 十连 → dict
core.operator_card("能天使")                    # 干员信息
core.get_archive("能天使")                     # 档案
core.get_voice("能天使")                       # 语音
core.get_story("0-10")                        # 剧情
core.recruit("user_id", "减速 特种")            # 公招
core.list_banners()                           # 卡池列表
```

## ⚠️ 免责声明

- 游戏数据与素材版权归 **鹰角网络 (Hypergryph)** 所有
- 数据来源于 [PRTS Wiki](https://prts.wiki)（CC BY-NC-SA 4.0）
- 本仓库**只含代码**，数据由用户自行爬取
- 本工具仅供学习交流，**禁止商用**；爬虫遵守 PRTS robots.txt 与限速要求

## 📄 许可证

代码：**GNU GPL v3**（copyleft —— 衍生作品必须同样开源，见 [LICENSE](LICENSE)）
