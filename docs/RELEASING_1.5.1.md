# Сборка и публикация Berserk 1.5.1

Получите актуальную `main`: скачайте Code → Download ZIP и распакуйте в новую папку.
Для git-клона сохраните ручные правки, затем выполните `git switch main` и `git pull --ff-only`.

В папке репозитория с `README.md`, `mods` и `tools` откройте PowerShell:

```powershell
py -3 .\tools\package_release.py
if ($LASTEXITCODE -ne 0) { throw "Сборка не прошла" }
explorer .\dist
```

Если команда `py` отсутствует, используйте `python`.
Скрипт заново создаёт `dist/`; не храните там посторонние файлы.

## Публикация через сайт

Откройте https://github.com/i0985/Berserk-Cata-DDA/releases/new

- Tag: `1.5.1`, Target: `main`.
- Release title: `Berserk Cata-DDA 1.5.1 — Armor & Arm Cannon Visual Fixes`.
- Описание: содержимое `docs/RELEASE_1.5.1.md` (английский → русский → китайский).
- Прикрепите три ZIP из `dist/` и опубликуйте релиз.

## Публикация через GitHub CLI

После входа через `gh auth login` следующая команда сразу публикует релиз:

```powershell
gh release create 1.5.1 .\dist\Berserk.zip .\dist\Berserk_chibi_tileset.zip .\dist\Berserk-CDDA-0.I-1.zip --repo i0985/Berserk-Cata-DDA --target main --title "Berserk Cata-DDA 1.5.1 — Armor & Arm Cannon Visual Fixes" --notes-file .\docs\RELEASE_1.5.1.md
```

Если релиз `1.5.1` уже существует, обновите его через страницу редактирования.
Изменения в `main` не обновляют прикреплённые ZIP автоматически: для нового содержимого нужна новая сборка и загрузка архивов.
