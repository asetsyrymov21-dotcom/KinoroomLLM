# =============================================================
#  deploy.ps1 — коммит и пуш (VPS деплоится через GitHub Actions)
#  Использование:
#    .\deploy.ps1 "сообщение коммита"
#    .\deploy.ps1              # сообщение по умолчанию: "deploy"
# =============================================================

param(
    [string]$Message = "deploy"
)

function info    { param($t) Write-Host "[deploy] $t" -ForegroundColor Green }
function warning { param($t) Write-Host "[deploy] $t" -ForegroundColor Yellow }
function fail    { param($t) Write-Host "[deploy] $t" -ForegroundColor Red; exit 1 }

# ── 1. Чистим lock-файлы если зависли ────────────────────────
foreach ($lock in @(".git\index.lock", ".git\HEAD.lock")) {
    if (Test-Path $lock) {
        warning "Удаляю зависший $lock..."
        Remove-Item $lock -Force
        info "Удалён."
    }
}

# ── 2. git add ────────────────────────────────────────────────
info "git add -A"
git add -A
if ($LASTEXITCODE -ne 0) { fail "git add завершился с ошибкой" }

# ── 3. git commit (пропускаем если нечего) ────────────────────
$status = git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    warning "Нечего коммитить, пропускаю commit."
} else {
    info "git commit: `"$Message`""
    git commit -m $Message
    if ($LASTEXITCODE -ne 0) { fail "git commit завершился с ошибкой" }
}

# ── 4. git push ───────────────────────────────────────────────
info "git push origin main"
git push origin main
if ($LASTEXITCODE -ne 0) { fail "git push завершился с ошибкой" }

info "✓ Запушено. GitHub Actions задеплоит на VPS автоматически."
info "Прогресс: https://github.com/asetsyrymov21-dotcom/KinoroomLLM/actions"
