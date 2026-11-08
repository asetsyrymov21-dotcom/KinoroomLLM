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

## Secret handling — mandatory

- Never commit or push real API keys, access tokens, passwords, private keys, credential URLs, or production configuration.
- Keep secrets in ignored local environment files or the GitHub Actions secrets store. Example/template files must contain placeholders only.
- Before every commit, scan the staged diff with Gitleaks using --pre-commit --staged --redact=100.
- Before every push or PR, scan every commit being published with Gitleaks using --log-opts=--all --redact=100.
- If the scanner is missing, fails, or finds a secret, stop. Never use --no-verify, bypass push protection, or add an allowlist to conceal a real secret.
- Stage explicit paths only. Never stage .env files, key files, private credential backups, or cleanup bundles.
- Never print secret values in logs, commands, reviews, screenshots, or PR descriptions.
- If a secret was committed, remove it from reachable history and report that revocation/rotation and GitHub cache/PR cleanup may still be required.
