Краткое руководство по запуску тестов и сбору покрытия кода

1) Установите зависимости для тестирования (если ещё не установлены):

```bash
python -m pip install -r requirements.txt
python -m pip install pytest pytest-asyncio pytest-cov
```

2) Запуск тестов:

```bash
pytest -q
```

3) Сбор отчёта покрытия (coverage) и вывод недостающего покрытия в консоль:

```bash
pytest --cov=src --cov-report=term-missing --maxfail=1 -q
```

4) Генерация HTML-отчёта покрытия:

```bash
pytest --cov=src --cov-report=html
# результат в ./htmlcov/index.html
```

Короткое описание процесса тестирования
- Тесты написаны с использованием pytest и pytest-asyncio для async-сервисов.
- В тестах используются мок-объекты (AsyncMock) для репозиториев и сессий БД — это делает тесты быстрыми и детерминированными.
- Для интеграционного тестирования потребуется поднять тестовую БД PostgreSQL и тестовый MinIO; это выходит за рамки текущих unit-тестов.
