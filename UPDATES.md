# Kinorum — Крупные обновления проекта

> Читать когда нужно понять что менялось в архитектуре или бизнес-логике.
> Не перечитывать при каждом запросе.

---

## Правила ведения файла

- Фиксировать только крупные изменения: новые модули, рефакторинг архитектуры, смена подходов
- Мелкие фиксы — не сюда (для них есть git log)
- Формат: дата, название, что изменилось, какие файлы затронуты, на что влияет

---

## [2026-04] Мультитенантность

**Что добавили:**
- Таблица `tenants`, поле `tenant_id` во всех основных таблицах (`bookings`, `halls`, `products`, `categories`, `orders`, `order_items`, `staff`, `stock_*`)
- `TenantScopedRepository` — базовый репозиторий с автофильтрацией по `tenant_id`
- Роли: `superadmin` (env), `admin` (таблица staff), `operator` (таблица staff)
- Панель `/admin` — React SPA с разделением по ролям
- JWT-авторизация через `staff`

**Миграция:** `009_add_multitenancy.py`

**Затронутые файлы:**
- Все модели в `app/models/`
- Все репозитории в `app/repositories/`
- `app/schemas/booking.py` — добавлено поле `user: BookingUserInfo` в `BookingRead`
- `app/api/v1/bookings.py`, `app/services/booking.py`

**Побочные эффекты:**
- Появилась ошибка MissingGreenlet при создании брони → см. `KNOWN_ISSUES.md #1`
- `User` остался глобальной таблицей без `tenant_id` (намеренно)

---

## [2026-04] Система лояльности

**Что добавили:**
- Таблица `loyalty_rules` — глобальная (без tenant_id)
- Скидка на бронь по количеству визитов (`discount_pct` в `bookings`)
- `LoyaltyService` применяет скидку при создании брони

**Миграция:** `004_categories_loyalty.py`

**Затронутые файлы:**
- `app/models/loyalty.py`, `app/services/loyalty.py`
- `app/schemas/booking.py`, `app/services/booking.py`

---

## [2026-04] История сеансов

**Что добавили:**
- Эндпоинт `GET /bookings/history` — все завершённые сеансы с деталями заказов
- Эндпоинт `GET /bookings/{id}/summary` — детали одного сеанса
- Схема `SessionHistoryRead` с вложенными заказами и товарами
- `extra_charge` в `bookings` — доплаты за сеанс

**Миграция:** `005_add_extra_charge.py`

**Затронутые файлы:**
- `app/schemas/booking.py`, `app/services/booking.py`, `app/repositories/booking.py`

---

## [2026-04] Open-ended бронирования

**Что добавили:**
- Флаг `is_open_ended` в `bookings` — бронь без фиксированного времени окончания
- При `complete()` считается реальная стоимость по `completed_at - start_time`

**Миграция:** `003_add_is_open_ended.py`

**Затронутые файлы:**
- `app/models/booking.py`, `app/services/booking.py`, `app/schemas/booking.py`

---
