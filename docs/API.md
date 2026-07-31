# ArkCore API 参考

> **纯净核心**：`ak_core.ArkCore` 是零依赖 bot 框架的纯净门面。任何 bot 框架、CLI、HTTP 客户端、网页脚本，只需把聊天命令/请求翻译成对它的调用，再把返回的 dict 拼成消息即可。输入是普通参数，输出是普通 dict，不掺任何框架。

## 初始化

```python
from ak_core import ArkCore

# 默认：数据目录取环境变量 AK_DATA_DIR（否则 ~/arknights-data）
core = ArkCore()

# 指定目录
core = ArkCore(data_dir="/path/to/data", user_data_dir="/path/to/userdata")
```

**数据目录结构**（由 akdata_crawler 生成）：
```
<data_dir>/
├── operators.json          # 干员全量
├── operator_index.json     # 查询索引
├── gacha_rules.json        # 寻访规则
├── banners/banners.json    # 卡池配置
├── recruit/                # 公招数据
├── archives/<key>.json     # 干员档案
├── voices/<key>.json       # 语音
├── stories/                # 剧情
└── avatars/<key>.png       # 头像
```

---

## 抽卡

### `core.list_banners() -> list[dict]`
返回全部卡池配置。

### `core.current_banner(user_id: str) -> dict`
返回用户当前所在卡池。

### `core.switch_banner(user_id: str, target: str) -> bool`
切换卡池，`target` 支持全名/部分匹配。成功返回 `True`。

### `core.pull(user_id: str, banner_name: str | None, count: int = 1) -> dict`
抽卡。`banner_name=None` 用用户当前池。

```python
r = core.pull("user_1", "标准轮换·卡池190", 10)
# 成功：
# {
#   "ok": True, "banner": "标准轮换·卡池190",
#   "results": [{"name": "...", "star": 6, "profession": "狙击", "key": "..."}],
#   "p6": 12, "soft_start": 51, "spark_pulls": 10,
#   "jade": 54000, "total_pulls": 30,
# }
# 失败（玉不足/超限）：
# {"ok": False, "error": "合成玉不足..."}
```

### `core.pity_info(user_id: str) -> dict`
各保底分组的 6★/5★ 计数。

### `core.spark(user_id: str) -> dict`
限定池 300 抽井兑换。`{"ok": True, "name": "限定干员"}` 或 `{"ok": False, "error": ...}`。

### `core.free_pull(user_id: str) -> dict`
限定池每日免费抽。

### `core.resources(user_id: str, topup: bool = False) -> dict`
查看/补充合成玉、源石。

---

## 干员查询

### `core.find_operator(keyword: str) -> dict | None`
按中文/英文/别名模糊查干员（返回完整 operators.json 条目）。

### `core.operator_card(name: str) -> dict | None`
干员信息卡（含头像本地路径）：
```python
{
  "name_zh": "能天使", "name_en": "Exusiai", "star": 6,
  "profession": "狙击", "subprofession": "速射手",
  "position": "远程位", "nation": "拉特兰", "race": "萨科塔",
  "tags": ["输出"], "obtain": [...], "avatar": "/path/to/avatars/能天使.png",
}
```

### `core.get_archive(name: str) -> dict | None`
干员档案（基础/履历/诊断/档案1-4）。

### `core.get_voice(name: str) -> dict | None`
语音记录：`{"name_zh": "...", "lines": [{"title": "...", "trigger": "...", "zh": "..."}]}`

### `core.get_story(keyword: str) -> dict | None`
剧情（主线/活动/密录）：
```python
{"stage": "0-10 困境", "lines": [{"type": "dialogue", "speaker": "阿米娅", "text": "..."}]}
```

---

## 公开招募

### `core.recruit(user_id: str, tags_str: str = "") -> dict`
- 空参数 → 随机 4 个标签：`{"ok": True, "suggest": [...]}`
- 带标签 → 抽干员：`{"ok": True, "operator": {...}, "tags": [...]}`
- 失败 → `{"ok": False, "error": ...}`

---

## 通用约定

- **所有方法返回 dict / list / None**，不抛框架相关异常
- `user_id` 由各框架从聊天事件中取（如 AstrBot `event.get_sender_id()`、NoneBot2 `event.get_user_id()`）
- 头像等文件路径返回**本地绝对路径**，由适配器负责转成框架的图片消息
- 长文本（档案/剧情）建议适配器按 ~1500 字分段发送
