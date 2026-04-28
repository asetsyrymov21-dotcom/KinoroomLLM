#!/bin/bash
# =============================================================
#  deploy.sh — коммит и пуш текущей ветки
#  Использование:
#    ./deploy.sh "сообщение коммита"
#    ./deploy.sh              # сообщение по умолчанию: "deploy"
# =============================================================

set -e

COMMIT_MSG="${1:-deploy}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[deploy]${NC} $1"; }
warning() { echo -e "${YELLOW}[deploy]${NC} $1"; }
fail()    { echo -e "${YELLOW}[deploy]${NC} $1"; exit 1; }

# ── 1. Проверяем ветку ────────────────────────────────────────
BRANCH="$(git branch --show-current)"
if [ -z "$BRANCH" ]; then
    fail "Не удалось определить текущую ветку"
fi
if [ "$BRANCH" = "main" ]; then
    fail "Прямой push в main запрещён. Создайте рабочую ветку и откройте PR."
fi
info "Текущая ветка: $BRANCH"

# ── 2. Чистим index.lock если завис ───────────────────────────
if [ -f ".git/index.lock" ]; then
    warning "Удаляю зависший .git/index.lock..."
    rm -f ".git/index.lock"
fi

# ── 3. Git: add → commit → push ───────────────────────────────
info "git add -A"
git add -A

if git diff --cached --quiet; then
    warning "Нечего коммитить, пропускаю commit."
else
    info "git commit: \"$COMMIT_MSG\""
    git commit -m "$COMMIT_MSG"
fi

info "git push origin $BRANCH"
git push origin "$BRANCH"

info "✓ Ветка запушена. Откройте PR в main для деплоя через GitHub Actions."
