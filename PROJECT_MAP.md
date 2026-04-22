# Kinorum — Карта проекта

> Backend для управления залами, бронированием и складом.  
> Stack: **FastAPI + SQLAlchemy (async) + PostgreSQL + Alembic + Docker**

---

## Точка входа

| Файл | Что делает |
|------|-----------|
| `app/main.py` | Создаёт FastAPI-приложение, подключает все роутеры, CORS, монтирует фронтенд на `/app` |
| `app/config.py` | Настройки через Pydantic Settings (`DATABASE_URL`, `DB_ECHO`), читает `.env` |
| `app/database.py` | Создаёт async engine, сессию (`AsyncSession`), базовый класс `Base` для моделей; функция `get_db` |
| `app/api/deps.py` | `get_session` — зависимость для инъекции сессии в роутеры |

---

## API — Роутеры (`app/api/v1/`)

Все роутеры подключены с префиксом `/api/v1`.

| Файл | Prefix | Теги | Основные эндпоинты |
|------|--------|------|--------------------|
| `app/api/v1/users.py` | `/users` | Users | `GET /by-telegram/{telegram_id}`, `POST /` |
| `app/api/v1/halls.py` | `/halls` | Halls | `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}` |
| `app/api/v1/categories.py` | `/categories` | Categories | `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` |
| `app/api/v1/products.py` | `/products` | Products | `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}` |
| `app/api/v1/bookings.py` | `/bookings` | Bookings | `POST /`, `GET /`, `GET /{id}`, `POST /{id}/activate`, `POST /{id}/complete`, `POST /{id}/cancel`, `GET /history` |
| `app/api/v1/stock.py` | `/stock` | Stock | `POST /receive`, `GET /halls/{hall_id}/inventory`, `GET /movements` |
| `app/api/v1/orders.py` | `/orders` | Orders | `POST /`, `GET /{id}`, `POST /{id}/items`, `POST /{id}/complete`, `POST /{id}/cancel` |
| `app/api/v1/loyalty.py` | `/loyalty` | Loyalty | `POST /rules`, `GET /rules`, `PATCH /rules/{id}`, `DELETE /rules/{id}`, `GET /users/{user_id}` |

---

## Бизнес-логика — Сервисы (`app/services/`)

Сервисы содержат всю логику, роутеры только вызывают их.

| Файл | Класс | Что делает |
|------|-------|-----------|
| `app/services/booking.py` | `BookingService` | **FLOW 1**: создание брони, переходы статусов `pending → active → completed/cancelled`, расчёт `total_price`, применение скидки лояльности |
| `app/services/order.py` | `OrderService` | **FLOW 2 + 3**: создание заказа на активную бронь, добавление позиций с резервом склада, complete (списание) / cancel (снятие резерва) |
| `app/services/stock.py` | `StockService` | Приход товара в зал (`receive`), просмотр остатков по залу |
| `app/services/hall.py` | `HallService` | CRUD залов, проверка уникальности имени |
| `app/services/product.py` | `ProductService` | CRUD товаров, проверка уникальности SKU |
| `app/services/category.py` | `CategoryService` | CRUD категорий меню |
| `app/services/loyalty.py` | `LoyaltyService` | CRUD правил, подсчёт визитов, применение награды к брони |

---

## Модели БД (`app/models/`)

| Файл | Модели | Таблицы | Ключевые поля |
|------|--------|---------|---------------|
| `app/models/user.py` | `User` | `users` | `telegram_id` (BigInt, unique), `name`, `phone` |
| `app/models/hall.py` | `Hall` | `halls` | `name` (unique), `capacity`, `price_per_hour`, `is_active` |
| `app/models/booking.py` | `Booking`, `BookingStatus` | `bookings` | `user_id`, `hall_id`, `start_time`, `end_time`, `status`, `total_price`, `completed_at`, `discount_pct`, `extra_charge` |
| `app/models/product.py` | `Product` | `products` | `name`, `sku` (unique), `price`, `cost_price`, `unit`, `is_active`, `category_id` |
| `app/models/category.py` | `Category` | `categories` | `name` (unique), `emoji`, `position`, `is_active` |
| `app/models/loyalty.py` | `LoyaltyRule`, `RewardType` | `loyalty_rules` | `visits_required`, `reward_type` (discount/free_booking), `reward_value`, `is_active` |
| `app/models/stock.py` | `StockLocation`, `StockBalance`, `StockMovement`, `MovementType` | `stock_locations`, `stock_balances`, `stock_movements` | `StockLocation` связывает hall+product; `StockBalance` хранит `quantity`/`reserved_quantity`; `StockMovement` — лог (receive/reserve/write_off/cancel_reserve) |
| `app/models/order.py` | `Order`, `OrderItem`, `OrderStatus` | `orders`, `order_items` | `Order.booking_id`, `OrderItem.product_id`, `quantity`, `price_at_order` |

---

## Схемы Pydantic (`app/schemas/`)

Каждый модуль зеркалит соответствующую модель:

| Файл | Схемы |
|------|-------|
| `app/schemas/user.py` | `UserCreate`, `UserRead` |
| `app/schemas/hall.py` | `HallCreate`, `HallUpdate`, `HallRead` |
| `app/schemas/booking.py` | `BookingCreate`, `BookingRead`, `SessionHistoryRead` |
| `app/schemas/product.py` | `ProductCreate`, `ProductUpdate`, `ProductRead` |
| `app/schemas/stock.py` | `StockReceiveRequest`, `StockBalanceRead`, `StockMovementRead`, `HallInventoryItem` |
| `app/schemas/order.py` | `OrderCreate`, `OrderRead`, `OrderItemAdd`, `OrderItemRead` |

---

## Репозитории (`app/repositories/`)

Чистые запросы к БД, без бизнес-логики. Каждый сервис использует свой репозиторий.

| Файл | Репозиторий | Назначение |
|------|-------------|-----------|
| `app/repositories/base.py` | `BaseRepository` | Общие методы: `get`, `get_all`, `create`, `update`, `delete` |
| `app/repositories/user.py` | `UserRepository` | `get_by_telegram_id` |
| `app/repositories/hall.py` | `HallRepository` | `get_by_name`, `list_active` |
| `app/repositories/booking.py` | `BookingRepository` | `list_by_status`, `list_by_hall`, `list_active_for_hall` |
| `app/repositories/product.py` | `ProductRepository` | `get_by_sku`, `list_active` |
| `app/repositories/stock.py` | `StockLocationRepository`, `StockBalanceRepository`, `StockMovementRepository` | Работа с остатками и логом движений |
| `app/repositories/order.py` | `OrderRepository` | `list_by_booking` |

---

## Миграции (`alembic/`)

| Файл | Ревизия | Что делает |
|------|---------|-----------|
| `alembic/env.py` | — | Настройка Alembic, подключение к БД |
| `alembic/versions/001_initial.py` | `001` | Начальная схема: все таблицы, индексы |
| `alembic/versions/002_add_completed_at.py` | `002` | Добавляет `completed_at` в таблицу `bookings` |
| `alembic/versions/003_add_is_open_ended.py` | `003` | Добавляет `is_open_ended` в `bookings` |
| `alembic/versions/004_categories_loyalty.py` | `004` | Таблицы `categories`, `loyalty_rules`; колонки `cost_price`/`category_id` в `products`; `discount_pct` в `bookings` |
| `alembic/versions/005_add_extra_charge.py` | `005` | Добавляет `extra_charge` (Numeric 10,2, nullable) в `bookings` |

Применить миграции: `alembic upgrade head`

---

## Фронтенд

| Файл | Что делает |
|------|-----------|
| `frontend/index.html` | Telegram Mini App — интерфейс для пользователя (бронирование зала) |
| `operator.html` | Интерфейс оператора — управление бронями, заказами, складом |

Фронтенд раздаётся FastAPI на пути `/app` (StaticFiles).

---

## Инфраструктура

| Файл | Назначение |
|------|-----------|
| `.env` | Локальные переменные среды (не в git) |
| `.env.example` | Пример конфига |
| `requirements.txt` | Python-зависимости: fastapi, uvicorn, sqlalchemy, asyncpg, alembic, pydantic, pydantic-settings |
| `Dockerfile` | Образ приложения |
| `docker-compose.yml` | 3 сервиса: `db` (postgres:15), `migrate` (alembic upgrade head), `api` (uvicorn :8001) |
| `alembic.ini` | Конфиг Alembic |

---

## Локальный запуск и доступ извне

- Приложение запускается на порту **8001**
- Публичный доступ: **Cloudflare Tunnel** (активный) + ngrok (запасной)
- Текущий URL Cloudflare: меняется при каждом перезапуске туннеля (`*.trycloudflare.com`)
- Операторка: `https://<текущий-url>/operator.html`
- Первичная настройка: `https://<текущий-url>/setup.html`
- Мини-апп (Telegram Web App): `https://<текущий-url>/app`
- API: `https://<текущий-url>/api/v1/`
- Ngrok статичный домен (запасной): **mercedes-ironic-rikki.ngrok-free.app**
- Аккаунт ngrok: olzhik882009@gmail.com (Plan: Free)

---

## Ключевые бизнес-флоу

```
FLOW 1 — Бронирование зала:
  POST /bookings/            → создать бронь (status: pending)
  POST /bookings/{id}/activate → активировать (pending → active)
  POST /bookings/{id}/complete → завершить + рассчитать стоимость (active → completed)
  POST /bookings/{id}/cancel  → отменить (pending/active → cancelled)

FLOW 2 — Заказ товаров (требует active booking):
  POST /orders/              → создать заказ для активной брони
  POST /orders/{id}/items    → добавить позицию → резерв товара на складе
  POST /orders/{id}/complete → списание с остатков
  POST /orders/{id}/cancel   → снятие резерва

FLOW 3 — Склад:
  POST /stock/receive        → приход товара в зал
  GET  /stock/halls/{id}/inventory → остатки по залу
  GET  /stock/movements      → лог движений
```

---

## Связи между сущностями

```
User ──< Booking >── Hall
                 └──< Order >── OrderItem >── Product
                                               │
Hall ──< StockLocation >── StockBalance        │
                      └──< StockMovement <─────┘
```
