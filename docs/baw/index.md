# IBM BAW: навыки для Codex

> **Статус: тестовые и непроверенные.** Навыки BAW исключены из основной установки. Полная проверка на IBM BPM/BAW не выполнена; результаты анализаторов требуют сверки с исходниками.

Адаптация 22 навыков из [ibmbpm/ibm-baw-skills-and-bob-modes](https://github.com/ibmbpm/ibm-baw-skills-and-bob-modes),
зафиксированная на ревизии `f8af103a9f1fb1074921ddf1e5d6b6d52f9ed5cb`.
Лицензия Apache-2.0 и сведения об источнике включены в каждый устанавливаемый каталог.
Это сторонняя адаптация, не официальный продукт IBM и не MCP-сервер.

## Каталог

| Навык | Назначение |
|---|---|
| [generate-baw-bpmn](generate-baw-bpmn.md) | Создать BPMN и XSD для импорта в IBM BAW из описания процесса или требований. |
| [generate-baw-business-objects](generate-baw-business-objects.md) | Создать или изменить бизнес-объекты IBM BAW в OpenAPI JSON либо упаковать их в TWX. |
| [create-baw-widget](create-baw-widget.md) | Создать или изменить Coach View IBM BAW и собрать локальный TWX toolkit. |
| [create-baw-portal](create-baw-portal.md) | Разработать портал задач IBM BAW или добавить BAW API в существующее веб-приложение. |
| [create-baw-external-task-ui](create-baw-external-task-ui.md) | Создать внешний интерфейс human task IBM BAW для открытия через Custom URL. |
| [baw-project-doc](baw-project-doc.md) | Документировать приложение IBM BAW по TWX, BPMN и XSD без подключения к серверу. |
| [baw-dependency-mapper](baw-dependency-mapper.md) | Найти использования переменной или Business Object в TWX IBM BAW и оценить влияние изменения. |
| [baw-toolkit-analyzer](baw-toolkit-analyzer.md) | Проанализировать зависимости toolkit, версии и использования артефактов в TWX IBM BAW. |
| [compare-baw-versions](compare-baw-versions.md) | Сравнить два TWX или две версии приложения IBM BAW по процессам, скриптам и настройкам. |
| [review-baw-code](review-baw-code.md) | Проверить JavaScript, HTML и CSS артефактов IBM BAW из TWX, файлов или переданного кода. |
| [audit-baw-readiness](audit-baw-readiness.md) | Оценить контрольные механизмы приложения IBM BAW по TWX и подготовить отчёт о пробелах. |
| [process-compliance-violation-detection](process-compliance-violation-detection.md) | Сопоставить приложение IBM BAW с переданными политиками и требованиями и найти подтверждённые расхождения. |
| [generate-baw-tests](generate-baw-tests.md) | Подготовить тесты процессов и Coach UI IBM BAW; выполнить согласованные сценарии на тестовом стенде. |
| [test-baw-service-flows](test-baw-service-flows.md) | Подготовить и выполнить тесты Service Flow IBM BAW по его контракту входов и выходов. |
| [baw-container-inventory](baw-container-inventory.md) | Показать и найти Process Apps и Toolkits на сервере IBM BAW с учётом пагинации. |
| [version-inspector](version-inspector.md) | Прочитать метаданные snapshot и версии приложения или toolkit IBM BAW. |
| [version-lifecycle-manager](version-lifecycle-manager.md) | Управлять snapshot и переменными окружения IBM BAW по явно выбранной операции. |
| [baw-deployment-manager](baw-deployment-manager.md) | Развернуть выбранный snapshot IBM BAW на указанном сервере и проверить статус установки. |
| [baw-export-import-helper](baw-export-import-helper.md) | Перенести приложения и toolkit IBM BAW между окружениями с проверкой зависимостей и порядка импорта. |
| [baw-endpoint-validation](baw-endpoint-validation.md) | Проверить TWX IBM BAW на адреса исходного окружения перед переносом на другой сервер. |
| [inspect-baw-processes](inspect-baw-processes.md) | Найти и исследовать экземпляры процессов IBM BAW; выполнить явно порученное действие над экземпляром. |
| [troubleshoot-baw-logs](troubleshoot-baw-logs.md) | Диагностировать ошибки IBM BAW по SystemOut.log, messages.log, trace.log, FFDC или данным экземпляра. |

## Установка

Используйте [наш установщик](../installation.md). Он копирует инструкции вместе
со скриптами и справочниками; режимы и установщик Bob не нужны.

```sh
python scripts/install.py --include-experimental --skill baw-project-doc --skill generate-baw-bpmn --project "C:/work/baw-project"
```

Для установки в личный каталог Codex укажите его явно:

```sh
python scripts/install.py --include-experimental --skill baw-project-doc --dest "C:/Users/your-name/.codex/skills"
```

Обычное меню, `--list` и `--all` не включают BAW. Для тестовой установки обязателен `--include-experimental`; с ним можно использовать `--list`, `--skill` или `--all`.
Для начала без сервера подходят генерация BPMN, документация и анализ локального TWX.
Наличие навыка не подключает BAW и не создаёт MCP-инструменты.

## Работа с файлами и сервером

Локальные помощники используют Python; для пакета BAW рекомендуем Python 3.10+
(отдельные upstream-модули используют современные аннотации типов).
Проверки портала используют Node.js. Зависимости генерируемого веб-приложения
определяются его стеком и устанавливаются отдельно в целевом проекте.

Передайте путь к TWX, BPMN/XSD, логу или коду и цель задачи. Если нужен сервер,
укажите версию BAW, точный URL с context root, приложение/snapshot и окружение.
Доступ к API зависит от версии и прав пользователя; поддержка старого IBM BPM
не гарантируется. Справочники upstream в том числе описывают API BAW 26.x.

Учётные данные настройте локально в переменных окружения или `.env` целевого
проекта (`BAW_BASE_URL`, `BAW_USERNAME`, `BAW_PASSWORD` либо механизм токена среды).
Не передавайте пароль в чат и не включайте `.env`, TWX с рабочими данными и логи
в публичный репозиторий. Агент читает секреты внутри HTTP-процесса без вывода.
Для частного центра сертификации настройте доверенный CA; проверка TLS сохранена.

Генерация тестов не запускает их на стенде. Импорт, deploy, изменение snapshot,
запуск процесса и завершение задач выполняются только в пределах явно порученного
действия. Наличие экспортированного или сгенерированного файла не означает его
сохранение в Process Designer.

## Что изменено для Codex

- Краткие русские описания для обнаружения навыков; подробные предметные workflow
  и справочники загружаются по мере необходимости.
- Заменены обязательные инструменты Bob и пути `.bob`; инструкции учитывают
  Windows, доступные инструменты Codex и локальные артефакты без подключения.
- Переработана работа с секретами, TLS, разрешениями и неизвестными MCP-возможностями.
- Исходные генераторы и анализаторы сохранены вместе с шаблонами и лицензиями.
- Пользовательские страницы вынесены в `docs/baw/`; инструкции для агентов
  и нужные им технические справочники остаются внутри навыков.

Локальные проверки не заменяют импорт и выполнение на вашей версии BAW.
Тестового стенда в этой адаптации нет: сетевые сценарии и прямое редактирование
артефактов Process Designer не объявляются проверенными.

[Общий каталог](../index.md)
