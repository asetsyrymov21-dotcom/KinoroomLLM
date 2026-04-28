# AGENTS.md

## Core rules
- Diagnose first, fix second
- Do not break tenant_id logic
- No large refactoring
- Max 3 files per change
- No direct push to main
- Production changes only via GitHub PR -> main -> GitHub Actions

## VPS access
- Diagnostics only by default
- Allowed: read logs/status/ports, check docker ps, curl health endpoints
- Forbidden without explicit emergency approval: edit files, change .env, run destructive commands, docker compose down -v, git reset --hard
- Manual VPS edits must not replace the normal GitHub Actions deploy path

## Modes
- Automation: diagnostics only
- Manual: targeted fixes only

## Live URLs
- Main domain: https://roompilot.kz
- Admin panel: https://roompilot.kz/admin
- Setup page: https://roompilot.kz/setup.html
- Telegram Mini App: https://app.roompilot.kz
- Mini App API: https://app.roompilot.kz/api/v1/
- Public API/docs: https://roompilot.kz/api/v1/ and https://roompilot.kz/docs
- Do not use old Cloudflare tunnel URLs as canonical links; they were temporary.

## Routing
- Debug -> ai/rules/debug.md
- Deploy -> ai/rules/git-deploy.md
- Tenant -> ai/rules/tenant.md
- Coding -> ai/rules/coding.md
- Automation -> ai/rules/automation.md
