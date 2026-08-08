<div align="center">

# Arknights Toolkit · 明日方舟数据系统

**纯 Python 的明日方舟数据工具箱 · 不用懂任何框架 · 装上就能玩**

[![PyPI](https://img.shields.io/badge/PyPI-1.3.1-blue)](https://pypi.org/project/arknights-datakit/)
[![Python](https://img.shields.io/pypi/pyversions/arknights-datakit)](https://pypi.org/project/arknights-datakit/)
[![License](https://img.shields.io/github/license/xianyu686/bot-ark-tools)](LICENSE)

**当前版本：`1.3.1`**（用 `python bump_version.py X.Y.Z` 发版，三处版本号自动同步）

</div>

装好之后，你能在命令行抽卡、查干员档案、看语音剧情，还能把它接进 QQ 机器人当"方舟小助手"。数据会自动从 [PRTS Wiki](https://prts.wiki) 抓取，**不用自己准备任何数据文件**。

---

## 🚀 三步上手（小白也能 5 分钟跑起来）

> 全程只要复制粘贴，不用懂代码。

**第 0 步 · 装 Python（已有可跳过）**
- 需要 **Python 3.9+**（Windows / macOS / Linux 都行）
- 没有就去 [python.org](https://www.python.org/downloads/) 下载安装，安装时**记得勾选 "Add Python to PATH"**

**第 1 步 · 安装**
```bash
pip install arknights-datakit
```

**第 2 步 · 同步数据（第一次要等几分钟，它会自动抓取干员/头像/档案/语音/公招/卡池）**
```bash
ark-tools sync all
```
> 数据默认存到 `~/arknights-data`，想换位置就设置环境变量 `AK_DATA_DIR`。
> 剧情是长任务、不在 `all` 里：需要时单独跑 `ark-tools sync stories --only main`。

**第 3 步 · 试一下**
```bash
ark-tools pull --user 1 --count 10    # 抽十连
ark-tools operator 能天使             # 查干员
ark-tools archive 能天使              # 查档案
ark-tools voice 能天使                # 查语音文本
```

✅ 完成！命令行就能玩明日方舟数据了。

> **可选的配置**：不配置也能跑。想改就复制 `config.example.json` 为 `config.json`
> 放在运行目录（或设环境变量 `AK_CONFIG` 指向它），支持：`data_dir` 数据目录、
> `daily_pull_limit` 每日抽卡上限（0=无限）、`starting_jade` 新用户初始玉、
> `crawler_interval_seconds` 爬虫限速。也可直接用环境变量 `AK_DATA_DIR` /
> `AK_DAILY_PULL_LIMIT` / `AK_STARTING_JADE` / `AK_CRAWLER_INTERVAL` 覆盖。

---

## 🎮 能干什么

- 🎰 **抽卡寻访** — 完全还原游戏的概率、软保底、限定池和井，抽起来跟游戏里一样
- 📇 **干员图鉴** — 查干员信息卡 + 头像
- 📜 **干员档案** — 履历 / 诊断 / 档案
- 🎤 **语音记录** — 全部台词文本
- 📖 **剧情** — 主线 / 活动 / 干员密录
- 🎯 **公开招募** — 还原游戏：选 1-3 个标签 + 选招募时间（0:10~9:00），空组合落到保底池，`公招记录` 查历史
- 🔄 **自动同步** — 增量爬取、断点续传，随时 `ark-tools sync all` 更新

---

## 💬 接进 QQ（可选）

命令行玩够了想让它进 QQ 群？两个办法，由简到繁：

### 方式一 · HTTP 服务（最简单，任何机器人框架都能调）
```bash
ark-tools server --port 8900
```
然后任何语言/框架发一条 HTTP 请求就能用：
```bash
curl "http://127.0.0.1:8900/chat" -d '{"user_id":"1","text":"十连"}'
```
接口说明见 [docs/API.md](docs/API.md)。

### 方式二 · 现成框架适配器（AstrBot / NoneBot2）
见下方「开发者专区」，复制一个文件就行，适配器只是个"薄壳"。

---

## 🧩 开发者专区

### 用 Python 直接调（核心 API）
```python
from ak_core import ArkCore

core = ArkCore()  # 数据目录取 AK_DATA_DIR（默认 ~/arknights-data）

core.pull("user_id", "标准轮换·卡池190", 10)   # 十连 → dict
core.operator_card("能天使")                    # 干员信息
core.get_archive("能天使")                     # 档案
core.get_voice("能天使")                       # 语音
core.get_story("0-10")                        # 剧情
core.recruit("user_id", "减速 特种")            # 公招（默认 9:00）
core.recruit("user_id", "资深干员 输出", "3:50")  # 公招并指定时间
core.recruit_history("user_id")                # 公招记录
core.list_banners()                           # 卡池列表
```

### 架构
```
ak_core 核心引擎（纯 Python，零框架依赖）
   ↑
CommandHandler 统一命令分发（ak_tools/commands.py）
   ↑                        ↑
CLI (ark-tools)      HTTP 微服务 / 适配器
   ↑
akdata_crawler 爬虫 → 数据目录
```
核心逻辑全在 `ak_core` + `CommandHandler`，**适配器只负责「喂一句话 → 收回复」**，所以任何框架都能接。

### 接 AstrBot
把 `adapters/astrbot/` 文件夹放进 AstrBot 的 `data/plugins/`，重启后群里就能用：
```
[唤醒词] 方舟 · 十连 · 卡池 · 干员 X · 档案 X · 语音 X · 剧情 X · 公招
```

### 接 NoneBot2
把 `adapters/nonebot2/plugins/ark_toolkit.py` 放进 `plugins/`（需 `pip install nonebot2 nonebot-adapter-onebot`）。

### 接入新框架
详见 [docs/ADAPTER.md](docs/ADAPTER.md) —— 5 步接入，核心逻辑一行不改。

---

## 📄 许可证与免责声明

- 代码采用 **GNU GPL v3**（copyleft，衍生作品必须同样开源，见 [LICENSE](LICENSE)）
- 游戏数据与素材版权归 **鹰角网络 (Hypergryph)** 所有
- 数据来源于 [PRTS Wiki](https://prts.wiki)（CC BY-NC-SA 4.0）
- 本仓库**只含代码**，不含任何游戏数据 / 图片 / 密钥
- 本工具仅供学习交流，**禁止商用**；爬虫遵守 PRTS robots.txt 与限速要求
