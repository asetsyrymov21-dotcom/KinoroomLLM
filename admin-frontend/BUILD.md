# Сборка admin панели

## Первая сборка

```bash
cd admin-frontend
npm install
npm run build
```

После этого появится папка `admin-dist/` в корне проекта.
FastAPI автоматически начнёт её раздавать на `/admin`.

## Разработка (dev-режим)

```bash
cd admin-frontend
npm install
npm run dev
```

Открывается на `http://localhost:5173/admin/`.
API-запросы автоматически проксируются на `http://localhost:8001`.

## После каждого изменения фронтенда

```bash
cd admin-frontend && npm run build
```

Закоммитить `admin-dist/` в git чтобы деплой на VPS не требовал npm.

## Деплой на VPS

Стандартный флоу:
```bash
git pull origin main
docker compose run --rm migrate
docker compose up -d --force-recreate api
```

Папка `admin-dist/` берётся из git — npm на сервере не нужен.

## .gitignore

В `admin-frontend/` добавлен `node_modules/` в gitignore.
Папка `admin-dist/` намеренно НЕ в gitignore — коммитится в репозиторий.
