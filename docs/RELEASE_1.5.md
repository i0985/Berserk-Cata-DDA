# Berserk Cata-DDA 1.5 — The Price of Rage

## English

The armor offers a way through the horde. Version 1.5 gives that power a price: a growing curse, uncertain shadows, and a short burst of rage followed by prolonged recovery.

### Changes

- Replaced continuous armor-induced bleeding with persistent curse tension, four visible stages, perception penalties, and recovery after removing all armor pieces. Resting without the armor speeds recovery.
- Added extra shadow waves at the two higher curse stages: attempts to spawn two or three shadows every 30 seconds, at a distance of 7–12 tiles. Each new shadow independently has a one-in-three chance of being a hallucination. Existing real-demon events remain active.
- Added automatic Berserk mode at high tension while wearing the chestplate: 150 seconds, +2 strength, +10 speed, and stamina support. Activation displays a popup; countdown messages appear every 30 seconds and every second during the final ten seconds.
- Ending the mode empties stamina, causes blood loss and applies three days of recovery (-2 strength, -15 speed). Reactivation also requires reduced tension and removing all six armor pieces. Removing all pieces during the rush ends it early and still applies the consequences.
- Added a lost-left-hand CBM and a single-shot prosthetic arm cannon. The cannon uses crafted powder charges instead of bionic energy. Installing the lost-hand CBM teaches the cannon CBM and ammunition recipes.
- Adjusted the true Guts sword for one-handed use; the fan-made sword retains its restrictions.
- Added a reversible, automatically known recipe to pack all six armor pieces for transport. Unpack them before wearing; this is a transport bundle, not a wearable one-piece suit.
- Added English source strings and Russian/Chinese translations for the new content; fixed prosthesis profession load order.

### Installation and status

Target: **CDDA 0.I-1**. Core mechanics and existing-save loading were tested in-game by the mod author; automated asset validation passed. This is not a claim of exhaustive testing on every language or tileset.

- `Berserk.zip`: main mod with UltiCa support. Enable **Berserk** only when using UltiCa.
- `Berserk_chibi_tileset.zip`: optional graphics addon for ChibiUltica / supported MSX+ and Undead tilesets.
- `Berserk-CDDA-0.I-1.zip`: both folders in one archive; the addon is still optional.

Extract the selected folders into `mods/` beside `cataclysm-tiles.exe`. Remove duplicate old copies from `data/mods/`. Keep a backup of your save before updating.

**Known issue:** fine alignment of UltiCa armor overlays remains under investigation. This release restores the settings from immediately before the latest per-piece adjustment (upper -15, lower -4); it does not claim to resolve the underlying visual issue. With the game closed, removing `cache/mods/Berserk/` clears generated caches after manual JSON changes.

The Eclipse dungeon is planned for a later update and is not included in 1.5.

## Русский

Броня даёт возможность прорваться сквозь орду. Версия 1.5 добавляет цену этой силы: растущее проклятие, настоящие и мнимые тени, короткую вспышку ярости и долгое восстановление.

### Изменения

- Постоянное кровотечение от брони заменено накоплением напряжения, четырьмя видимыми стадиями, штрафами к восприятию и восстановлением после снятия всех частей. Отдых без брони ускоряет восстановление; перезаход не обнуляет напряжение.
- На двух высоких стадиях каждые 30 секунд происходят попытки создать две или три дополнительные тени на расстоянии 7–12 клеток. Для каждой отдельно шанс галлюцинации составляет 1/3. Прежние события настоящих демонов продолжают работать.
- Режим Берсерка автоматически включается при высоком напряжении и надетом нагруднике: 150 секунд, +2 к силе, +10 к скорости и поддержание выносливости. Добавлены всплывающее предупреждение и отсчёт каждые 30 секунд, а в последние десять секунд — каждую секунду.
- По завершении выносливость обнуляется, происходит потеря крови и начинается трёхдневное восстановление (-2 к силе, -15 к скорости). Для повторной активации также нужно снизить напряжение и снять все шесть частей брони. Полное снятие во время ярости завершает её досрочно с теми же последствиями.
- Добавлены КБМ утраченной левой кисти и однозарядная рука-пушка. Пушка расходует создаваемые пороховые заряды, а не энергию бионики. Установка КБМ утраченной кисти открывает рецепты КБМ пушки и зарядов.
- Истинный меч Гатса приспособлен для одной руки; ограничения фанатского меча сохранены.
- Добавлен известный с начала обратимый рецепт упаковки шести частей брони. Перед надеванием комплект нужно распаковать: это упаковка для переноски, а не цельный надеваемый костюм.
- Для нового контента подготовлены английские строки и русский/китайский переводы; исправлен порядок загрузки профессии с протезом.

### Установка и состояние

Целевая версия — **CDDA 0.I-1**. Автор проверил основные механики и загрузку старого сохранения в игре; автоматическая проверка ресурсов пройдена. Полная проверка всех языков и тайлсетов не заявляется.

Для UltiCa достаточно `Berserk.zip` и включённого мода **Berserk**. `Berserk_chibi_tileset.zip` — отдельный графический аддон для ChibiUltica и поддерживаемых MSX+/Undead. `Berserk-CDDA-0.I-1.zip` содержит обе папки; аддон остаётся необязательным.

Распакуйте выбранные папки в `mods/` рядом с `cataclysm-tiles.exe`, уберите старые дубликаты из `data/mods/`. Перед обновлением сохраните резервную копию сохранения.

**Известная проблема:** точное выравнивание брони UltiCa ещё исследуется. Возвращены настройки перед последней раздельной подгонкой: верх -15, низ -4. Причина визуального смещения пока не устранена. После ручного изменения JSON можно при закрытой игре удалить созданный ею кэш `cache/mods/Berserk/`.

Подземелье Затмения запланировано на будущее и в 1.5 не входит.

## 中文

狂战士铠甲能帮助你杀出尸群，但力量也有代价。1.5 版本加入了逐渐加深的诅咒、真实与虚幻交织的暗影，以及短暂的狂暴和漫长的恢复期。

### 更新内容

- 移除了穿戴铠甲造成的持续流血，改为可保存的诅咒紧张度、四个可见阶段和感知惩罚。脱下全部铠甲后逐渐恢复，休息可加快恢复；重新读档不会清除紧张度。
- 在较高的两个阶段，每 30 秒尝试在 7–12 格外生成两只或三只额外暗影。每只暗影独立有 1/3 的概率是幻觉。原有的真实恶魔事件继续生效。
- 穿着胸甲且紧张度足够高时自动进入狂暴模式：持续 150 秒，力量 +2、速度 +10，并维持一定耐力。启动时显示弹窗，每 30 秒提示剩余时间，最后十秒逐秒倒计时。
- 狂暴结束后耐力归零、血量减少，并进入三天恢复期（力量 -2、速度 -15）。再次触发还需要降低紧张度并脱下全部六件铠甲。狂暴期间脱下全套铠甲会提前结束效果，但仍需承担后果。
- 加入失去左手的 CBM 和单发义肢手炮。手炮使用可制作的火药弹药，不消耗生化能量。安装失去左手的 CBM 后会学会手炮 CBM 和弹药配方。
- 调整了真正的格斯之剑，使其适合单手使用；仿制剑保留原有限制。
- 新增初始即可掌握的可逆打包配方，可将六件铠甲打包携带。穿戴前必须拆包；它不是可直接穿戴的一体式护甲。
- 新内容提供英文原文、俄文和中文翻译，并修复了义肢职业的加载顺序。

### 安装与已知问题

目标游戏版本：**CDDA 0.I-1**。模组作者已在游戏中测试核心机制和旧存档加载，资源自动检查已通过；并非所有语言和材质包都经过全面游戏测试。

UltiCa 用户只需安装 `Berserk.zip` 并启用 **Berserk**。`Berserk_chibi_tileset.zip` 是供 ChibiUltica 及支持的 MSX+/Undead 材质包使用的可选图像扩展。`Berserk-CDDA-0.I-1.zip` 包含两个文件夹，但扩展仍是可选的。

将所需文件夹解压到与 `cataclysm-tiles.exe` 同级的 `mods/` 中，移除 `data/mods/` 内重复的旧版模组。更新前请备份存档。

**已知问题：** UltiCa 铠甲的像素对齐仍在调查。本次恢复到最近一次逐件调整之前的设置（上半身 -15，下半身 -4），并未宣称解决视觉偏移的根因。手动修改 JSON 后，可在关闭游戏时删除生成的 `cache/mods/Berserk/` 缓存。

蚀之地下城留待后续更新，不包含在 1.5 中。
