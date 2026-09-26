# Berserk Cata-DDA 1.5.1 — Armor & Arm Cannon Visual Fixes

## English

A graphics and packaging update for **CDDA 0.I-1**.

- Updated the upper Berserker armor sprites for the UltiCa character model, with separate positioning for the helmet, chestplate, gloves and armguards.
- Added distinct closed and open prosthetic arm cannon sprites. Activating and retracting the CBM now switches its appearance correctly.
- Separated the cannon states into individual tileset JSON files to avoid a CDDA 0.I-1 loading error.
- Fixed release packaging: archives now preserve file modification times, preventing the old fixed timestamp from making CDDA silently reuse obsolete JSON caches.

**Updating:** close the game, replace the mod folders inside `mods/` beside `cataclysm-tiles.exe`, then delete the generated caches `cache/mods/Berserk/` and, if present, `cache/mods/Berserk_chibi_tileset/`. Keep `save/` and `config/`. Remove duplicate copies of the mod from `data/mods/`. For UltiCa, enable only the main **Berserk** mod.

The mod author confirmed correct sprite positioning and cannon state switching, then confirmed successful operation after clearing the old cache. Automated JSON, asset and packaging checks passed. Gameplay mechanics are unchanged in this patch.

## Русский

Обновление графики и упаковки мода для **CDDA 0.I-1**.

- Обновлены верхние спрайты брони Берсерка под модель персонажа UltiCa. Положение шлема, нагрудника, перчаток и наручей настраивается отдельно.
- Добавлены отдельные спрайты закрытой и открытой руки-пушки. Активация и отключение КБМ корректно меняют её внешний вид.
- Состояния руки-пушки разделены на отдельные JSON тайлсетов, чтобы устранить ошибку загрузки в CDDA 0.I-1.
- Исправлен упаковщик: архивы сохраняют даты изменения файлов. Прежняя одинаковая дата больше не заставляет игру незаметно использовать устаревший кэш JSON.

**Обновление:** закройте игру, замените папки мода в `mods/` рядом с `cataclysm-tiles.exe`, затем удалите созданный игрой кэш `cache/mods/Berserk/` и, если есть, `cache/mods/Berserk_chibi_tileset/`. Сохраните `save/` и `config/`. Уберите дубликаты мода из `data/mods/`. Для UltiCa включайте только основной мод **Berserk**.

Автор мода подтвердил правильное положение спрайтов и переключение состояний руки-пушки, а затем успешную работу после очистки старого кэша. Автоматические проверки JSON, ресурсов и упаковщика пройдены. Игровые механики в этом исправлении не менялись.

## 中文

适用于 **CDDA 0.I-1** 的图像与打包修复更新。

- 更新了狂战士铠甲上半身的精灵图，以适配 UltiCa 的角色模型；头盔、胸甲、手套和护臂可分别调整位置。
- 为义肢手炮加入了独立的关闭与展开精灵图。启用和关闭 CBM 时，现在会正确切换外观。
- 将手炮的两个状态拆分为独立的材质包 JSON 文件，修复 CDDA 0.I-1 中的加载错误。
- 修复打包脚本：压缩包现在保留文件修改时间，避免旧的固定时间戳导致游戏无提示地重复使用过时的 JSON 缓存。

**更新方法：**关闭游戏，替换与 `cataclysm-tiles.exe` 同级的 `mods/` 中的模组文件夹，然后删除游戏生成的缓存 `cache/mods/Berserk/` 和（如果存在）`cache/mods/Berserk_chibi_tileset/`。保留 `save/` 和 `config/`。移除 `data/mods/` 内重复的模组。使用 UltiCa 时只需启用主模组 **Berserk**。

模组作者已确认精灵图位置和手炮状态切换正确，并确认清除旧缓存后游戏运行正常。JSON、资源和打包自动检查均已通过。本次补丁未更改游戏机制。
