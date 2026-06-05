# Berserk mod 简体中文翻译

## 文件

- `lang/po/Berserk.pot` — 翻译模板（俄文 msgid）
- `lang/po/zh_CN.po` — 简体中文（用 Poedit 编辑）
- `lang/mo/zh_CN/LC_MESSAGES/Berserk.mo` — 游戏读取的二进制（由 Poedit 编译）

`Berserk.mo` 文件名必须与 `modinfo.json` 里的 `"id": "Berserk"` 一致。

## Poedit 用法

1. 用 Poedit 打开 `lang/po/zh_CN.po`
2. 检查/修改译文，保存
3. 菜单 **Catalog → Compile to MO**（或保存时自动编译）
4. 确认生成 `lang/mo/zh_CN/LC_MESSAGES/Berserk.mo`

## 进游戏测试

1. 游戏语言设为 **简体中文 (zh_CN)**
2. 将整份 mod 复制到 `mods/Berserk-Cata-DDA/`（不要带 `.git`）
3. 启用 Berserk mod

## 重要：msgctxt

CDDA 0.I 翻译查找带 **上下文**（`msgctxt`），不能只写裸 `msgid`：

| JSON 类型 | msgctxt |
|-----------|---------|
| 职业名称 | `profession_male` / `profession_female`（各一条，同文也要重复） |
| 职业描述 | `prof_desc_male` / `prof_desc_female` |
| 场景名称 | `scenario_male` / `scenario_female` |
| 场景描述 | `scen_desc_male` / `scen_desc_female` |
| 出生点名称 | `start_name` |
| 物品 / mod 说明 / EOC 弹窗 | 无 context |

手写的 `.pot` 若缺少上述 `msgctxt`，游戏里职业/场景仍会显示俄文。应用 CDDA 的 `lang/extract_json_strings.py` 重新提取，或按上表补全后再编译 `.mo`。

## 批次

- **A（已完成）**：mod 说明、职业、物品、场景
- **B（已完成）**：怪物、法术、战斗台词、效果、弱点、EOC 弹窗
