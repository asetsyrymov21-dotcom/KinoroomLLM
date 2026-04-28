# Git Deploy Rules

## Before deploy:
- Check current branch
- Check uncommitted changes
- Check latest CI status
- Confirm target environment
- Deploy path is GitHub PR -> main -> GitHub Actions

## Forbidden:
- direct push to main
- deploy with failing tests
- deploy without rollback path
- manual production edits on VPS unless explicitly approved as emergency rollback/fix
- editing VPS .env or secrets through an agent
