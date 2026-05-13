# Frappe Bench — Aries ERP

## Start the dev server

```bash
cd /Users/harithoppil/Desktop/game/erp-aries/frappe-bench && env/bin/bench start
```

Runs on http://localhost:8000

## PostgreSQL 15 (local)

- DB: `aries_site`
- User: `aries_frappe` / Password: `aries_pass`
- Port: 5432 (socket: /tmp)
- Service: `brew services start postgresql@15`

## Redis

- Default port 6379
- Service: `brew services start redis`

> **Note:** PostgreSQL and Redis are managed via `brew services` and auto-start on login — no need to manually start them each time.

## Site

- Site name: `aries.local`

## App source locations

| App | Path |
|---|---|
| Frappe | `apps/frappe/` |
| ERPNext | `apps/erpnext/` |
| erpnext_ai | `apps/erpnext_ai/` (symlink → `/Users/harithoppil/Desktop/game/erp-aries/erpnext_ai/`) |
