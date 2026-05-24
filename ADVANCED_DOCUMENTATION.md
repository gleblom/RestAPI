# 📊 Расширенная документация: Примеры и диаграммы

## Содержание
1. [Диаграмма архитектуры](#диаграмма-архитектуры)
2. [Сценарии использования](#сценарии-использования)
3. [Обработка ошибок](#обработка-ошибок)
4. [Оптимизация и производительность](#оптимизация-и-производительность)

---

## Диаграмма архитектуры

### Слои приложения

```
┌──────────────────────────────────────────────────────────────┐
│                    HTTP Endpoints (routers/)                 │
│  GET/POST /documents, /routes, /users, /approvals, etc       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    Business Logic (services/)                │
│  - approval_service.py (согласование)                        │
│  - document_service.py (документы)                           │
│  - route_service.py (маршруты)                              │
│  - user_service.py, company_service.py и т.д.               │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                 Data Access Layer (repositories/)            │
│  - DocumentRepository.get_document_by_id()                   │
│  - RouteRepository.get_route()                               │
│  - NotificationRepository.create_notification()              │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              Database & External Services                    │
│  - PostgreSQL (sqlalchemy ORM)                               │
│  - MinIO (хранилище файлов)                                  │
│  - Email (отправка уведомлений)                              │
└──────────────────────────────────────────────────────────────┘
```

### Поток данных при согласовании

```
┌─────────────────┐
│ Клиент отправляет│
│ документ на      │
│ согласование     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ POST /documents/{id}/submit              │ ← Endpoint (router)
│ { "route_id": 5 }                       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ submit_document_service()                       │ ← Service layer
│ 1. Валидация документа (автор?)                │
│ 2. Валидация маршрута                          │
│ 3. Найти первый узел маршрута                  │
│ 4. Создать DocumentApproval запись             │
│ 5. Создать Notification                        │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ DocumentRepository.get_document_by_id()       │ ← Repository
│ RouteRepository.get_route()                  │
│ DocumentRepository.create_document_approval() │
│ NotificationRepository.create_notification() │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ PostgreSQL                                  │
│ INSERT INTO document_approvals (...)        │
│ INSERT INTO notifications (...)             │
│ UPDATE documents SET status_id=3, ...       │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Ответ клиенту: Document (200)  │
│ со статусом IN_PROGRESS        │
└────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ Согласующему отправляется уведомление    │
│ (in-app + push notification)              │
└──────────────────────────────────────────┘
```

---

## Сценарии использования

### Сценарий 1: Простое линейное согласование

**Описание:** Документ проходит по линейному маршруту: Начальник → Финдиректор → Директор

#### Маршрут структура
```
RouteNode 1 (step_index=0) → Начальник (Ева)
         ↓
RouteNode 2 (step_index=1) → Финдиректор (Борис)
         ↓
RouteNode 3 (step_index=2) → Директор (Анна)
```

#### Последовательность операций

```
1️⃣  Автор (Петр) создает документ
    POST /documents/create
    └─→ Document(id=DOC-001, title="Квартальный отчет", status=DRAFT)

2️⃣  Петр загружает файл (версия 1)
    POST /documents/DOC-001/versions
    └─→ DocumentVersion(version_number=1)

3️⃣  Петр отправляет на согласование по маршруту 5
    POST /documents/DOC-001/submit { "route_id": 5 }
    └─→ submit_document_service():
        ├─ Document.status = IN_PROGRESS
        ├─ Document.current_step_index = 0
        ├─ Document.route_id = 5
        ├─ DocumentApproval(approver=Ева, step_index=0, is_approved=null)
        └─ Notification("Document requires your approval") → Ева

4️⃣  Ева одобрила документ
    POST /documents/DOC-001/approve
    └─→ approve_document_service():
        ├─ DocumentApproval(step_index=0).is_approved = TRUE
        ├─ Document.current_step_index = 1
        ├─ DocumentApproval(approver=Борис, step_index=1, is_approved=null)
        └─ Notification("Document requires your approval") → Борис

5️⃣  Борис одобрил документ
    POST /documents/DOC-001/approve
    └─→ approve_document_service():
        ├─ DocumentApproval(step_index=1).is_approved = TRUE
        ├─ Document.current_step_index = 2
        ├─ DocumentApproval(approver=Анна, step_index=2, is_approved=null)
        └─ Notification("Document requires your approval") → Анна

6️⃣  Анна (последний согласующий) одобрила документ
    POST /documents/DOC-001/approve
    └─→ approve_document_service():
        ├─ DocumentApproval(step_index=2).is_approved = TRUE
        ├─ Document.status = PUBLISHED          ✅ КОНЕЦ МАРШРУТА!
        └─ Notification("Document has been published") → Петр

✅ РЕЗУЛЬТАТ: Документ опубликован, видим всем в компании
```

#### Диаграмма состояний

```
Петр (автор)
    │
    ├─ DRAFT (с версией)
    │
    └─ IN_PROGRESS, step=0
        │
        ├─ Ева одобрила
        │
        ├─ IN_PROGRESS, step=1
        │   │
        │   ├─ Борис одобрил
        │   │
        │   └─ IN_PROGRESS, step=2
        │       │
        │       ├─ Анна одобрила
        │       │
        │       └─ PUBLISHED ✅
```

---

### Сценарий 2: Отклонение и доработка

**Описание:** Документ на согласовании был отклонен согласующим. Автор загружает новую версию и отправляет повторно.

```
1️⃣  Документ отправлен на согласование (как в сценарии 1, шаги 1-3)
    └─→ Document(status=IN_PROGRESS, step=0)

2️⃣  Ева ОТКЛОНИЛА документ с комментарием
    POST /documents/DOC-001/reject
    {
        "comment": "Требуются правки в разделе 2: уточнить финансовые показатели"
    }
    └─→ reject_document_service():
        ├─ DocumentApproval(step_index=0).is_approved = FALSE
        ├─ DocumentApproval(step_index=0).comment = "Требуются правки..."
        ├─ Document.status = RETURNED           ❌ Возвращен
        └─ Notification("Document rejected: Требуются правки...") → Петр

3️⃣  Петр (автор) видит, что документ возвращен
    GET /documents/DOC-001
    └─→ Response: status=RETURNED, current_step_index=0

4️⃣  Петр загружает новую версию документа
    POST /documents/DOC-001/versions
    {
        "storage_object_name": "documents/DOC-001-v2.pdf",
        ...
    }
    └─→ create_document_version_service():
        ├─ DocumentVersion(version_number=2)
        ├─ Document.status = DRAFT              ✅ Возвращено в черновик
        ├─ Document.current_step_index = 0
        └─ История согласования (version_number=1) остается в БД

5️⃣  Петр отправляет новую версию на согласование ЗАНОВО
    POST /documents/DOC-001/submit { "route_id": 5 }
    └─→ submit_document_service():
        ├─ Document.status = IN_PROGRESS
        ├─ Document.current_step_index = 0
        ├─ DocumentApproval(version_id=2, approver=Ева, step=0)
        └─ Notification() → Ева

6️⃣  Ева рассматривает версию 2 и одобряет
    POST /documents/DOC-001/approve
    └─→ Документ переходит на следующий этап (как в сценарии 1)

✅ РЕЗУЛЬТАТ: Документ прошел повторное согласование
```

#### Ключевые моменты

⚠️ **Версионирование:** При отклонении старая версия (1) остается в истории. Система отслеживает, какая версия на каком этапе согласования находилась.

⚠️ **Сброс статуса:** При загрузке новой версии документ автоматически переходит в DRAFT и step_index сбрасывается на 0.

⚠️ **Новая запись согласования:** Для версии 2 создается отдельная запись DocumentApproval с version_id=2.

---

### Сценарий 3: Параллельное согласование (не поддерживается)

**Важно:** Текущая система **НЕ поддерживает параллельные ветви**!

```
❌ НЕПРАВИЛЬНО (будет ошибка):

RouteNode 1 (step=0) 
    ├─→ RouteNode 2 (step=1)
    └─→ RouteNode 3 (step=1)    ← Две ветви!

При попытке одобрить узел 1 система проверит:
    next_nodes = get_next_route_nodes(route_id=5, node_id=1)
    if len(next_nodes) > 1:
        raise HTTPException(409, "Parallel branches not supported")
```

**Решение:** Использовать последовательные этапы с разными step_index

```
✅ ПРАВИЛЬНО:

RouteNode 1 (step=0) 
    ├─→ RouteNode 2 (step=1)
            └─→ RouteNode 3 (step=2)
```

---

## Обработка ошибок

### HTTP Статус-коды

| Код | Ошибка | Пример сценария |
|-----|--------|-----------------|
| 400 | Bad Request | Отправка документа без версий |
| 403 | Forbidden | Не автор документа пытается отправить |
| 404 | Not Found | Документ с таким ID не существует |
| 409 | Conflict | Повторное согласование уже согласованного этапа |
| 500 | Internal Server Error | Ошибка в БД (обработано с откатом транзакции) |

### Типичные ошибки и решения

#### ❌ "Document is not attached to an approval route"
```
Причина: Документ не отправлен на согласование (route_id = null)
Решение: Сначала отправить документ через submit_document_service()
```

#### ❌ "This step was already processed"
```
Причина: Этап уже согласован (is_approved != null)
Решение: Проверить, что документ находится на текущем этапе
```

#### ❌ "You are not the current approver"
```
Причина: Пользователь не является согласующим этапа
Решение: Убедиться, что правильный пользователь согласует документ
```

#### ❌ "Route graph contains a cycle"
```
Причина: При добавлении ребра образовался цикл в графе маршрута
Решение: Использовать линейные маршруты (каждый узел → max 1 потомок)
```

---

## Оптимизация и производительность

### N+1 Query проблема

Система использует `selectinload` в некоторых местах, но может быть оптимизирована:

```python
# ❌ МЕДЛЕННО (N+1):
for approval in approvals:
    print(approval.approver.full_name)  # N запросов!

# ✅ БЫСТРО:
# Использовать selectinload при запросе:
result = await db.execute(
    select(DocumentApproval)
    .options(selectinload(DocumentApproval.approver))
)
```

### Индексы БД

Рекомендуемые индексы для оптимизации:

```sql
-- Для быстрого поиска документов
CREATE INDEX ix_documents_search 
ON documents(status_id, category_id, created_at);

-- Для быстрого получения согласований по документу
CREATE INDEX ix_approvals_by_document 
ON document_approvals(document_id, version_id);

-- Для получения узлов маршрута
CREATE INDEX ix_route_nodes_by_step 
ON route_nodes(route_id, step_index);

-- Для поиска уведомлений пользователя
CREATE INDEX ix_notifications_by_user 
ON notifications(user_id, created_at DESC);
```

### Асинхронность и масштабируемость

Приложение использует асинхронные операции:
- ✅ Обработка множественных одновременных запросов
- ✅ Неблокирующие операции с БД
- ✅ Асинхронная отправка уведомлений

Рекомендации:
- Запустить несколько worker'ов (uvicorn workers или gunicorn)
- Использовать connection pooling (SQLAlchemy AsyncPool)
- Кэшировать часто запрашиваемые данные (маршруты, справочники)

---

## 📋 Checklist для разработчика

### При добавлении новой функции согласования

- [ ] Проверена валидация входных данных
- [ ] Проверены права доступа (компания, роль, статус)
- [ ] Операция выполнится в одной транзакции (commit/rollback)
- [ ] Обработаны все возможные HTTP ошибки
- [ ] Созданы уведомления для соответствующих пользователей
- [ ] Обновлено поле `updated_at` в документе
- [ ] Написаны unit/integration тесты
- [ ] Обновлена документация

### При добавлении нового маршрута

- [ ] Валидирована ацикличность графа
- [ ] Проверены права пользователя на компанию
- [ ] Протестирована с разными конфигурациями узлов и рёбер
- [ ] Документирована структура в DOCUMENTATION.md

---

## 🔍 Отладка и логирование

### Критические точки для логирования

```python
# При отправке на согласование
logger.info(f"Document {document_id} submitted to route {route_id} by {user_id}")

# При согласовании
logger.info(f"Document {document_id} approved by {user_id} at step {current_step}")

# При отклонении (сохраняем причину!)
logger.warning(f"Document {document_id} rejected by {user_id}: {comment}")

# При ошибках БД
logger.error(f"Database error: {str(e)}", exc_info=True)
```

### Трассировка документа через систему

```sql
-- Получить полную историю документа
SELECT 
    da.id,
    da.step_index,
    da.is_approved,
    da.comment,
    da.created_at,
    u.full_name as approver_name,
    dv.version_number
FROM document_approvals da
JOIN document_versions dv ON da.version_id = dv.id
JOIN users u ON da.approver_id = u.id
WHERE da.document_id = 'DOC-001'
ORDER BY da.created_at DESC;

-- Результат показывает полный процесс согласования:
-- версия 1: отклонено, версия 2: одобрено → PUBLISHED
```

---

## 📞 Решение часто встречающихся проблем

### Проблема: Документ "зависает" на этапе согласования

**Диагностика:**
```sql
-- Проверить, где находится документ
SELECT status_id, current_step_index, route_id 
FROM documents 
WHERE id = 'DOC-001';

-- Проверить, есть ли согласующий на этом этапе
SELECT rn.* FROM route_nodes rn
WHERE rn.route_id = ? AND rn.step_index = ?;

-- Проверить, кто должен согласовать
SELECT u.full_name, u.email 
FROM route_nodes rn
JOIN users u ON rn.approver_id = u.id
WHERE rn.route_id = ? AND rn.step_index = ?;
```

**Решение:** Проверить, работает ли согласующий, отправить ему напоминание.

---

### Проблема: Маршрут удалить не получается

**Причина:** Маршрут используется активным документом

**Решение:**
```sql
-- Найти все документы с этим маршрутом
SELECT * FROM documents WHERE route_id = ?;

-- Завершить процесс согласования или отклонить документы
-- Затем удалить маршрут
DELETE FROM approval_routes WHERE id = ?;
```

---

## 📈 Мониторинг и метрики

### Рекомендуемые метрики для отслеживания

1. **Среднее время согласования документа**
   ```sql
   SELECT AVG(EXTRACT(EPOCH FROM (d.updated_at - d.created_at))) 
   FROM documents d 
   WHERE status_id = 1;  -- Опубликованные
   ```

2. **Процент отклонений документов**
   ```sql
   SELECT 
       COUNT(*) FILTER (WHERE is_approved = false) * 100.0 / COUNT(*) as rejection_rate
   FROM document_approvals;
   ```

3. **Среднее количество версий до публикации**
   ```sql
   SELECT AVG(version_count) 
   FROM (
       SELECT document_id, COUNT(*) as version_count 
       FROM document_versions 
       GROUP BY document_id
   ) t;
   ```

