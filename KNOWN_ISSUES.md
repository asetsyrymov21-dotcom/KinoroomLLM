# Kinorum — Известные ошибки и решения

> Читать только когда что-то сломалось и неясно почему.
> Не перечитывать при каждом запросе.

---

## Правила ведения файла

- Добавлять ошибку сюда после того как она решена — с описанием причины и фикса
- Писать кратко: симптом → причина → решение
- Если ошибка повторилась в изменённом виде — дополнять существующую запись, не дублировать

---

## 1. MissingGreenlet при сериализации Booking

**Симптом:**
```
fastapi.exceptions.ResponseValidationError
MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here
loc: ('response', 'user')
```

**Причина:**
SQLAlchemy не загружает relationship `Booking.user` при создании брони. После `flush()` + `refresh()` объект попадает в identity map без загруженных relations. При сериализации Pydantic обращается к `booking.user`, SQLAlchemy пытается сделать синхронную ленивую загрузку в async-контексте — падает.

**Решение:**
В `BookingRepository.get_with_user()` добавить `.execution_options(populate_existing=True)` — это заставляет SQLAlchemy перезаписать объект из SELECT и применить `selectinload` даже если объект уже есть в identity map.

В `BookingRepository.get_by_user()` добавить `selectinload(Booking.user)` — там его не было вообще.

**Файлы:** `app/repositories/booking.py`

**Появилось после:** внедрения мультитенантности (добавление поля `user` в `BookingRead`)

---

## 2. Деплой проходит успешно, но код на VPS не обновляется

**Симптом:**
GitHub Actions показывает ✅, контейнер перезапустился, но старая ошибка осталась. Docker показывает `COPY . . → CACHED`.

**Причина:**
`git pull` на VPS падает с `fatal: Need to specify how to reconcile divergent branches` — ветки разошлись (например, кто-то коммитил напрямую на VPS). `appleboy/ssh-action` без `script_stop: true` продолжает выполнение после ошибки. Docker пересобирает образ из старого кода, кеш остаётся.

**Решение:**
1. На VPS вручную:
```bash
cd /opt/kinoroom
git fetch origin
git reset --hard origin/main
```
2. В `deploy.yml` заменить `git pull origin main` на `git fetch origin && git reset --hard origin/main`, добавить `script_stop: true`.

**Файлы:** `.github/workflows/deploy.yml`

---

## 3. API не стартует — отсутствуют переменные в .env на VPS

**Симптом:**
API падает при старте или работает с дефолтными небезопасными значениями (слабый SECRET_KEY, дефолтный пароль суперадмина). Подключение к БД может падать с ошибкой аутентификации.

**Причина:**
При первоначальной настройке VPS `.env` не был синхронизирован с локальным. Отсутствовали переменные: `POSTGRES_PASSWORD`, `SECRET_KEY`, `SUPERADMIN_USERNAME`, `SUPERADMIN_PASSWORD`. PostgreSQL при этом работал со старым паролем, не совпадающим с `DATABASE_URL`.

**Решение:**
1. Обновить `/opt/kinoroom/.env` на VPS (вставить актуальные значения из локального `.env`):
```bash
cat > /opt/kinoroom/.env << 'EOF'
POSTGRES_PASSWORD=...
DATABASE_URL=postgresql+asyncpg://postgres:...@db:5432/kinorum
SECRET_KEY=...
SUPERADMIN_USERNAME=...
SUPERADMIN_PASSWORD=...
EOF
```
2. Сбросить пароль PostgreSQL чтобы совпадал с `POSTGRES_PASSWORD`:
```bash
docker exec -it kinoroom-db-1 psql -U postgres -c "ALTER USER postgres WITH PASSWORD '...';"
```
3. Задеплоить **локально** через `./deploy.ps1 "..."` — не на VPS.

**Важно:** `deploy.ps1` — это Windows/PowerShell-скрипт. На VPS он не работает (`-bash: Permission denied`). Запускать только на локальной машине.

---

## 4. docker compose / docker-compose не работает на VPS

**Симптом:**
`docker compose` или `docker-compose` возвращает ошибку или не найден.

**Причина:**
На VPS не установлен плагин Docker Compose.

**Решение:**
```bash
apt-get update && apt-get install -y docker-compose-plugin
docker compose version  # проверить
```

**Управление контейнерами вручную (без compose):**
```bash
docker logs kinoroom-api-1 --tail=100
docker ps
docker restart kinoroom-api-1
```

---
