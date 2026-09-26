# Сборка и публикация Berserk 1.5

Сначала получите свежую main: скачайте Code → Download ZIP и распакуйте в новую папку. Если используете git-клон, выполните `git switch main` и `git pull --ff-only`, сохранив свои ручные изменения заранее.

Откройте папку репозитория, где находятся README.md, mods и tools. В адресной строке Проводника напишите `powershell` и нажмите Enter.

## Собрать архивы

Нужен установленный Python 3:

```powershell
py -3 .\tools\package_release.py
if ($LASTEXITCODE -ne 0) { throw "Сборка не прошла" }
explorer .\dist
```

Если команда `py` не найдена, используйте `python .\tools\package_release.py`. Скрипт сам проверяет ресурсы и заново создаёт папку dist. Другие нужные файлы в dist не храните.

## Опубликовать через сайт

Откройте https://github.com/i0985/Berserk-Cata-DDA/releases/new

- Tag: `v1.5`, Target: `main`.
- Release title: `Berserk Cata-DDA 1.5 — The Price of Rage`.
- Вставьте содержимое docs/RELEASE_1.5.md в описание.
- Прикрепите три ZIP из dist; нажмите Publish release, когда будете готовы.

## Либо опубликовать через GitHub CLI

Нужны установленный GitHub CLI и выполненный вход (`gh auth login`). Следующая команда создаёт и публикует релиз сразу; запускайте её только когда готовы. Используйте архивы из свежей main без локальных правок.

```powershell
gh release create v1.5 .\dist\Berserk.zip .\dist\Berserk_chibi_tileset.zip .\dist\Berserk-CDDA-0.I-1.zip --repo i0985/Berserk-Cata-DDA --target main --title "Berserk Cata-DDA 1.5 — The Price of Rage" --notes-file .\docs\RELEASE_1.5.md
```

Если релиз v1.5 уже существует, не создавайте его повторно: откройте его редактирование на сайте и загрузите нужные файлы.

Документация команды: https://cli.github.com/manual/gh_release_create
