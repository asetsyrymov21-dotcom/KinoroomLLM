# =============================================================
#  deploy.ps1 — коммит и пуш текущей ветки
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

# ── 1. Проверяем ветку ───────────────────────────────────────
$Branch = git branch --show-current
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Branch)) {
    fail "Не удалось определить текущую ветку"
}
if ($Branch -eq "main") {
    fail "Прямой push в main запрещён. Создайте рабочую ветку и откройте PR."
}
info "Текущая ветка: $Branch"

# ── 2. Чистим lock-файлы если зависли ────────────────────────
foreach ($lock in @(".git\index.lock", ".git\HEAD.lock")) {
    if (Test-Path $lock) {
        warning "Удаляю зависший $lock..."
        Remove-Item $lock -Force
        info "Удалён."
    }
}

# ── 3. git add ────────────────────────────────────────────────
info "git add -A"
git add -A
if ($LASTEXITCODE -ne 0) { fail "git add завершился с ошибкой" }

# ── 4. git commit (пропускаем если нечего) ────────────────────
$status = git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    warning "Нечего коммитить, пропускаю commit."
} else {
    info "git commit: `"$Message`""
    git commit -m $Message
    if ($LASTEXITCODE -ne 0) { fail "git commit завершился с ошибкой" }
}

# ── 5. git push ───────────────────────────────────────────────
info "git push origin $Branch"
git push origin $Branch
if ($LASTEXITCODE -ne 0) { fail "git push завершился с ошибкой" }

info "✓ Ветка запушена. Откройте PR в main для деплоя через GitHub Actions."
info "Прогресс: https://github.com/asetsyrymov21-dotcom/KinoroomLLM/actions"
