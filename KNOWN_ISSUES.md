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

## 3. docker compose / docker-compose не работает на VPS

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
