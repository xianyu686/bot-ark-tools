# 明日方舟数据系统 (Arknights Toolkit)

一个**框架无关**的明日方舟数据工具箱：完整复刻游戏寻访机制 + 干员图鉴/档案/语音/剧情/公招，配合 PRTS Wiki 爬虫自动维护数据。

> ⚠️ **版权声明（必读）**
> 本仓库**只包含代码，不包含任何游戏数据/图片素材**。
> - 明日方舟及其全部游戏素材版权归 **鹰角网络 (Hypergryph)** 所有
> - 数据来自 [PRTS Wiki](https://prts.wiki)（CC BY-NC-SA 4.0）
> - 数据由用户**自行运行爬虫从 PRTS 获取**，本仓库不附带任何游戏数据
> - 本项目仅用于个人学习与交流，**禁止商用**

## ✨ 功能

- 🎰 **寻访抽卡** — 完全复刻游戏机制：
  - 基础概率 6★2% / 5★8% / 4★50% / 3★40%
  - 6★ 软保底（51 抽起 +2%/抽，99 抽必出）
  - 十连/前 10 抽 5★ 保底
  - 限定池双 UP 权重 + 300 抽井
  - 标准选调 150/300、联动 120 保底
  - 中坚寻访独立保底、跨池继承规则
- 📇 **干员图鉴** — 干员信息卡 + 头像
- 📜 **干员档案** — 完整档案（基础/履历/诊断/档案1-4）
- 🎤 **语音记录** — 全部台词文本
- 📖 **剧情** — 主线 / 活动 / 干员密录
- 🎯 **公开招募** — tag 组合锁定稀有度
- 🔄 **资源同步** — 从 PRTS 增量爬取，断点续爬

## 🏗️ 架构

```
┌──────────────────────────────────────────────┐
│  ak_core       核心引擎（纯 Python，框架无关）     │
│                抽卡/档案/语音/剧情/公招/用户数据    │
└──────────────────────────────────────────────┘
        ▲ 调用                    ▲ 调用
┌──────────────────┐      ┌──────────────────────────┐
│ astrbot_adapter  │      │ (可扩展) NoneBot2/Koishi…  │
│ AstrBot 适配器    │      │ 各框架写一个薄适配器即可     │
└──────────────────┘      └──────────────────────────┘
        ▲ 读数据
┌──────────────────────────────────────────────┐
│  akdata_crawler   PRTS Wiki 爬虫                │
│  生成 D:\AKData（干员/卡池/档案/语音/剧情/公招）    │
└──────────────────────────────────────────────┘
```

**设计原则**：
- `ak_core` 不依赖任何 bot 框架 —— 输入普通参数，返回普通 dict
- 适配器只是「翻译层」—— 聊天命令 → 调核心 → 拼消息
- 数据与代码分离 —— 仓库不含数据，用户自己爬

## 📦 安装（给别人部署的步骤）

```bash
git clone https://github.com/xianyu686/bot-ark-tools
cd bot-ark-tools

# 方式 A：常规
pip install -r requirements.txt
# 方式 B：装成包（推荐，import ak_core 直接可用）
pip install -e .

# 指定数据目录（可选，默认 ~/arknights-data）
#  export AK_DATA_DIR=/path/to/your/data    (Linux/Mac)
#  set  AK_DATA_DIR=D:\your\data             (Windows)
```

## 🚀 使用

### 1. 生成数据（运行爬虫）

```bash
cd bot-ark-tools
python -m akdata_crawler.run operators    # 干员全量（423）
python -m akdata_crawler.run avatars      # 头像
python -m akdata_crawler.run archives     # 干员档案
python -m akdata_crawler.run voices       # 语音文本
python -m akdata_crawler.run recruit      # 公招数据
python -m akdata_crawler.run banners      # 卡池配置
python -m akdata_crawler.run stories      # 剧情（长任务，可 --only main）
# 或一键：
python -m akdata_crawler.run all
```

数据写入 `AK_DATA_DIR`（默认 `~/arknights-data`），增量同步、断点续爬。
爬虫需要能访问 PRTS Wiki（国内建议开代理）。

### 2. 接入 bot

**AstrBot**：把 `astrbot_adapter/` 放入 `data/plugins/`，重启后可用：
```
阿米娅 方舟      # 查看菜单
阿米娅 十连      # 抽卡
阿米娅 干员 能天使 # 图鉴+头像
阿米娅 档案 能天使
阿米娅 语音 能天使
阿米娅 剧情 0-1
阿米娅 公招 减速 特种
阿米娅 同步 干员 # 同步资源
```

**其他框架**：实例化 `ArkCore`，把命令翻译成调用即可（见 `ak_core/core.py` 的 API）。

## 🔧 核心 API

```python
from ak_core import ArkCore

core = ArkCore(data_dir="D:/AKData", user_data_dir="D:/AKData/userdata")

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
- 本工具仅供学习交流，禁止用于商业用途
- 爬虫遵守 PRTS robots.txt 与限速要求

## 📄 许可证

代码：MIT License（见 [LICENSE](LICENSE)）
