# baw-container-inventory

> **Статус: тестовые и непроверенные.** Навыки BAW исключены из основной установки. Полная проверка на IBM BPM/BAW не выполнена; результаты анализаторов требуют сверки с исходниками.

Показать и найти Process Apps и Toolkits на сервере IBM BAW с учётом пагинации.

## Использование

```text
Используй $baw-container-inventory: Покажи список toolkit на указанном тестовом сервере BAW.
```

## Что учитывать

Только чтение. Загружай все страницы перед подсчётом; scripts/process_containers.py обрабатывает уже полученный JSON. Не смешивай containers приложений с контейнерами Kubernetes.

[Установка и подключение BAW](index.md) · [Инструкция для агента](../../skills/baw-operations/baw-container-inventory/SKILL.md)
