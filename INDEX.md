# 📚 Индекс документации REST API

## 🗂️ Структура документации

Полная документация находится в трёх основных файлах:

### 1. **DOCUMENTATION.md** — Основная документация
   - 📖 Начните отсюда
   - Обзор архитектуры системы
   - Подробное описание критических функций согласования
   - Полный API reference с примерами

   **Основные разделы:**
   - [Обзор архитектуры](DOCUMENTATION.md#обзор-архитектуры)
   - [КЛЮЧЕВОЙ МОДУЛЬ: Согласование документов](DOCUMENTATION.md#ключевой-модуль-согласование-документов) ⭐⭐⭐
     - `submit_document_service()` — Отправить на согласование
     - `approve_document_service()` — Согласовать
     - `reject_document_service()` — Отклонить
   - [Жизненный цикл документа](DOCUMENTATION.md#жизненный-цикл-документа)
   - [API Endpoints](DOCUMENTATION.md#api-endpoints)

---

### 2. **ADVANCED_DOCUMENTATION.md** — Расширенная документация
   - 🎓 Для опытных разработчиков
   - Диаграммы архитектуры
   - Подробные сценарии использования
   - Обработка ошибок и отладка
   - Оптимизация и производительность

   **Основные разделы:**
   - [Сценарии использования](ADVANCED_DOCUMENTATION.md#сценарии-использования)
     - Сценарий 1: Простое линейное согласование
     - Сценарий 2: Отклонение и доработка
     - Сценарий 3: Параллельное согласование (не поддерживается)
   - [Диаграммы](ADVANCED_DOCUMENTATION.md#диаграмма-архитектуры)
   - [Решение проблем](ADVANCED_DOCUMENTATION.md#-решение-часто-встречающихся-проблем)

---

### 3. **DOCSTRING_EXAMPLES.md** — Примеры документирования кода
   - 💻 Для встраивания в исходный код
   - Готовые docstring'ы для ключевых функций
   - Стиль и соглашения документирования

---

## 🎯 Навигация по функциональности

### 📄 Согласование документов (КЛЮЧЕВОЙ МОДУЛЬ)

| Функция | Сложность | Описание | Ссылка |
|---------|-----------|---------|--------|
| `submit_document_service()` | ⭐⭐⭐⭐⭐ | Отправить документ на согласование | [DOCUMENTATION.md#-сложная-логика-submit_document_service](DOCUMENTATION.md#-сложная-логика-submit_document_service) |
| `approve_document_service()` | ⭐⭐⭐⭐⭐ | Согласовать документ и перейти на следующий этап | [DOCUMENTATION.md#-сложная-логика-approve_document_service](DOCUMENTATION.md#-сложная-логика-approve_document_service) |
| `reject_document_service()` | ⭐⭐⭐⭐ | Отклонить документ и вернуть автору | [DOCUMENTATION.md#-сложная-логика-reject_document_service](DOCUMENTATION.md#-сложная-логика-reject_document_service) |

### 📋 Управление документами

| Функция | Сложность | Описание | Ссылка |
|---------|-----------|---------|--------|
| `create_document_service()` | ⭐⭐ | Создать новый документ в статусе DRAFT | [DOCUMENTATION.md#create_document_service](DOCUMENTATION.md#create_document_service) |
| `create_document_version_service()` | ⭐⭐⭐ | Загрузить версию документа | [DOCUMENTATION.md#create_document_version_service](DOCUMENTATION.md#create_document_version_service) |
| `get_document_service()` | ⭐⭐⭐ | Получить документ с проверкой доступа | [DOCUMENTATION.md#get_document_service](DOCUMENTATION.md#get_document_service) |
| `list_documents_service()` | ⭐⭐⭐ | Список документов с фильтрацией | [DOCUMENTATION.md#list_documents_service](DOCUMENTATION.md#list_documents_service) |

### 🛣️ Управление маршрутами

| Функция | Сложность | Описание | Ссылка |
|---------|-----------|---------|--------|
| `create_route_service()` | ⭐ | Создать маршрут согласования | [DOCUMENTATION.md#create_route_service](DOCUMENTATION.md#create_route_service) |
| `add_node_service()` | ⭐⭐ | Добавить узел (этап согласования) | [DOCUMENTATION.md#add_node_service](DOCUMENTATION.md#add_node_service) |
| `add_edge_service()` | ⭐⭐⭐ | Добавить ребро (связь между этапами) | [DOCUMENTATION.md#add_edge_service](DOCUMENTATION.md#add_edge_service) |
| `_validate_acyclic()` | ⭐⭐ | Валидировать ацикличность графа | [DOCUMENTATION.md#_validate_acyclic](DOCUMENTATION.md#_validate_acyclic) |
| `get_route_graph_service()` | ⭐⭐⭐⭐ | Получить граф для визуализации | [DOCUMENTATION.md#get_route_graph_service](DOCUMENTATION.md#get_route_graph_service) |

---

## 🔍 Быстрые ответы на вопросы

### ❓ Как работает согласование документов?
**→** [DOCUMENTATION.md#-сложная-логика-submit_document_service](DOCUMENTATION.md#-сложная-логика-submit_document_service) + [Сценарий 1](ADVANCED_DOCUMENTATION.md#сценарий-1-простое-линейное-согласование)

### ❓ Что происходит, если согласующий отклоняет документ?
**→** [DOCUMENTATION.md#-сложная-логика-reject_document_service](DOCUMENTATION.md#-сложная-логика-reject_document_service) + [Сценарий 2](ADVANCED_DOCUMENTATION.md#сценарий-2-отклонение-и-доработка)

### ❓ Какие ошибки могут произойти при согласовании?
**→** [ADVANCED_DOCUMENTATION.md#обработка-ошибок](ADVANCED_DOCUMENTATION.md#обработка-ошибок)

### ❓ Как добавить новый этап в маршрут?
**→** [DOCUMENTATION.md#api-endpoints](DOCUMENTATION.md#api-endpoints) → POST `/routes/{route_id}/nodes`

### ❓ Почему система не поддерживает параллельные согласования?
**→** [ADVANCED_DOCUMENTATION.md#сценарий-3-параллельное-согласование-не-поддерживается](ADVANCED_DOCUMENTATION.md#сценарий-3-параллельное-согласование-не-поддерживается)

### ❓ Как работает контроль доступа к документам?
**→** [DOCUMENTATION.md#get_document_service](DOCUMENTATION.md#get_document_service)

### ❓ Какие метрики я должен отслеживать?
**→** [ADVANCED_DOCUMENTATION.md#-мониторинг-и-метрики](ADVANCED_DOCUMENTATION.md#-мониторинг-и-метрики)

---

## 📊 Ключевые концепции

### Статусы документа
```
DRAFT (2)          → начальный статус, видит только автор
IN_PROGRESS (3)    → на согласовании
PUBLISHED (1)      → согласован, видят все
RETURNED (4)       → отклонен, ждет доработки
```

### Маршрут согласования
- **DAG структура** (Directed Acyclic Graph) — граф без циклов
- **RouteNode** — этап с назначенным согласующим
- **RouteEdge** — связь между этапами
- **Линейные маршруты** — каждый узел имеет ≤ 1 потомка

### Версионирование
- Все версии документа сохраняются
- Согласования привязаны к версии
- При загрузке новой версии статус → DRAFT
- История согласований видна при просмотре

### Контроль доступа
- **Автор** видит всё (черновики, согласования, историю)
- **Опубликованные** видят все в компании
- **Опубликованные в отделе** видят в своём отделе
- Изоляция по **company_id**

---

## 🛠️ Для разработчиков

### Встроить docstring'ы в код
1. Откройте файл `DOCSTRING_EXAMPLES.md`
2. Выберите функцию, которую хотите задокументировать
3. Скопируйте docstring из примера
4. Вставьте в исходный код функции

### Добавить новую функцию
1. Прочитайте раздел о похожей функции в DOCUMENTATION.md
2. Следуйте тем же соглашениям
3. Добавьте docstring из DOCSTRING_EXAMPLES.md
4. Обновите API reference в DOCUMENTATION.md

### Расширить систему согласования
1. Прочитайте полностью [ADVANCED_DOCUMENTATION.md](ADVANCED_DOCUMENTATION.md)
2. Используйте сценарии как основу для новых функций
3. Убедитесь в атомарности транзакций
4. Добавьте обработку ошибок
5. Протестируйте с несколькими согласующими

---

## 🎓 Обучающий материал

### Для новичков
1. **Шаг 1:** Прочитайте [DOCUMENTATION.md#обзор-архитектуры](DOCUMENTATION.md#обзор-архитектуры)
2. **Шаг 2:** Посмотрите [ADVANCED_DOCUMENTATION.md#диаграмма-архитектуры](ADVANCED_DOCUMENTATION.md#диаграмма-архитектуры)
3. **Шаг 3:** Прочитайте [Сценарий 1](ADVANCED_DOCUMENTATION.md#сценарий-1-простое-линейное-согласование) для понимания процесса
4. **Шаг 4:** Изучите код функции `approve_document_service()` с docstring'ом

### Для тестировщиков
1. Прочитайте [ADVANCED_DOCUMENTATION.md#-решение-часто-встречающихся-проблем](ADVANCED_DOCUMENTATION.md#-решение-часто-встречающихся-проблем)
2. Используйте сценарии для написания тест-кейсов
3. Проверьте обработку ошибок из раздела [ADVANCED_DOCUMENTATION.md#обработка-ошибок](ADVANCED_DOCUMENTATION.md#обработка-ошибок)

### Для DevOps/Monitoring
1. Прочитайте [ADVANCED_DOCUMENTATION.md#-мониторинг-и-метрики](ADVANCED_DOCUMENTATION.md#-мониторинг-и-метрики)
2. Настройте логирование согласно разделу [ADVANCED_DOCUMENTATION.md#-отладка-и-логирование](ADVANCED_DOCUMENTATION.md#-отладка-и-логирование)
3. Используйте SQL запросы для отслеживания документов

---

## 📋 Краткая справка по API

### Согласование
```
POST /documents/{id}/submit           # Отправить на согласование
POST /documents/{id}/approve          # Согласовать
POST /documents/{id}/reject           # Отклонить
```

### Документы
```
POST /documents/create                # Создать
GET  /documents/{id}                  # Получить
GET  /documents                       # Список (с фильтрацией)
POST /documents/{id}/versions         # Загрузить версию
GET  /documents/{id}/versions         # История версий
```

### Маршруты
```
POST /routes                          # Создать маршрут
GET  /routes/{id}                     # Получить маршрут
POST /routes/{id}/nodes               # Добавить узел
POST /routes/{id}/edges               # Добавить ребро
GET  /routes/{id}/graph               # Получить граф для визуализации
```

---

## 🔗 Внешние ссылки

- **ТЗ проекта:** Прикреплено в этом же репозитории в описании ТЗ
- **Модель данных:** Смотрите `src/models/`
- **Примеры запросов:** DOCUMENTATION.md → API Endpoints

---

## ✅ Чеклист для ознакомления

- [ ] Прочитаны разделы DOCUMENTATION.md:
  - [ ] Обзор архитектуры
  - [ ] Все три функции согласования
  - [ ] Жизненный цикл документа
- [ ] Изучены сценарии в ADVANCED_DOCUMENTATION.md
- [ ] Понятны все HTTP коды ошибок
- [ ] Знаете, как работает версионирование
- [ ] Понимаете статусы документа
- [ ] Знаете ограничения (нет параллельных ветвей)

---

## 📞 Вопросы и обновления

Документация актуальна на **12 мая 2026 г.**

При обновлении кода обновляйте:
1. Исходные docstring'ы (в src/)
2. DOCUMENTATION.md (если меняется API или логика)
3. ADVANCED_DOCUMENTATION.md (если добавляются новые сценарии)
4. Этот файл INDEX.md (если добавляются новые разделы)
