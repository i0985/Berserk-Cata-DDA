# Установка New Horizon 3.1.0-dev

Это предварительная сборка от 4 октября 2026, а не подтверждённый финальный релиз.
Рабочая цель — CDDA 0.I-1; версия игрока — `cdda-0.I-2026-09-19-2324`.
Инструкция относится к портативной Windows-сборке; в других установках нужен
пользовательский каталог модов CDDA.

1. Закройте игру. Перед проверкой старого мира сохраните копию его сохранения.
2. Уберите прежние папки именно этого мода: `mods/Berserk/` и
   `mods/Berserk_chibi_tileset/`. Если их дубликаты есть в `data/mods/`, уберите
   и их: старая копия может получить приоритет. Не накладывайте новые файлы поверх
   старых. Остальные моды, `save/` и `config/` остаются на месте.
3. Из архива скопируйте `Berserk/` в пользовательский `mods/` рядом с
   `cataclysm-tiles.exe`. Итоговый путь: `<CDDA>/mods/Berserk/modinfo.json`.
   Папка `documentation/` в архиве предназначена для чтения, не для установки.
4. Для UltiCa (`UltimateCataclysm`) включите только **Berserk**.
   Для ChibiUltica / поддерживаемых MSX+ / Undead People установите рядом
   `Berserk_chibi_tileset/` и включите оба мода в мире.
5. При переходе с прежних предварительных архивов удалите только созданный
   игрой кэш этих модов: `<CDDA>/cache/mods/Berserk/` и, если есть,
   `<CDDA>/cache/mods/Berserk_chibi_tileset/`. CDDA создаст его заново.
   Не удаляйте сохранения или весь каталог игры.
6. Полностью перезапустите CDDA. В списке модов должна быть версия `3.1.0-dev`.
   Если видна 1.5.1, сначала найдите вторую установленную копию.

Каталоги переводов уже включены. Для русского ожидается
`mods/Berserk/lang/mo/ru/LC_MESSAGES/Berserk.mo`, для китайского —
`mods/Berserk/lang/mo/zh_CN/LC_MESSAGES/Berserk.mo`.
Их загрузку после обновления нужно проверять в игре. JSON и переводы должны
принадлежать одной сборке; не смешивайте папки из нескольких архивов.

Новые планировки строятся при новой локальной генерации. Посещённый ранее
дом или логово не перестраивается автоматически ради нового оформления.
Сохранённые цели используются на прежних координатах. Поэтому старый вариант
карты сам по себе не доказывает ошибку установки.

## English

Close CDDA and keep a copy of an existing save before the later playtest.
Replace the two mod folders completely; remove duplicate copies from
`data/mods/`. Extract the chosen folders into the user `mods/` beside the
portable game executable. Install only `Berserk` for UltiCa; add the optional
package for its listed tilesets. The final main path is
`<CDDA>/mods/Berserk/modinfo.json`. `documentation/` is for reading only.
Remove the generated caches for these two mods when updating from earlier
development archives, then restart. Keep saves and configuration untouched.
Existing local maps are preserved; the new layout appears on newly generated
sites. This development build still needs a full playthrough.

## 简体中文

先关闭游戏，并在之后测试旧世界前备份存档。完整替换这两个模组文件夹，移除
`data/mods/` 中的重复副本。将选用的文件夹解压到便携版游戏程序旁的用户
`mods/` 目录。UltiCa 只启用 `Berserk`；其他已列出的图块集还需可选包。
主文件应位于 `<CDDA>/mods/Berserk/modinfo.json`。`documentation/` 仅供阅读。
从旧开发包更新时，删除这两个模组对应的自动生成缓存并重启；不要删除存档
或配置。已生成的局部地图会保留，新布局在新生成的地点出现。当前开发版仍需
完整游戏流程验证。
