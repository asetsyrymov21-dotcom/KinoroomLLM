#!/bin/bash
# =============================================================
#  deploy.sh — коммит и пуш (VPS деплоится автоматически)
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

# ── 1. Чистим index.lock если завис ───────────────────────────
if [ -f ".git/index.lock" ]; then
    warning "Удаляю зависший .git/index.lock..."
    rm -f ".git/index.lock"
fi

# ── 2. Git: add → commit → push ───────────────────────────────
info "git add -A"
git add -A

if git diff --cached --quiet; then
    warning "Нечего коммитить, пропускаю commit."
else
    info "git commit: \"$COMMIT_MSG\""
    git commit -m "$COMMIT_MSG"
fi

info "git push origin main"
git push origin main

info "✓ Запушено. VPS задеплоится автоматически."
