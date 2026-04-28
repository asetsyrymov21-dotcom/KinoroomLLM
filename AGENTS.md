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

## Routing
- Debug -> ai/rules/debug.md
- Deploy -> ai/rules/git-deploy.md
- Tenant -> ai/rules/tenant.md
- Coding -> ai/rules/coding.md
- Automation -> ai/rules/automation.md
