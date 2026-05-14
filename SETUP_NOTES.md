# Sandbox Setup Notes — Bringing up Frappe + erp-ui + Headless Chrome

This file documents the actual hurdles hit while bringing the stack up in a fresh Linux sandbox (Ubuntu 24.04 / Python 3.13 / no display server) so the next person doesn't burn the same hour. Read top-to-bottom before running anything.

## 1. PostgreSQL (pre-installed but down)

```bash
pg_lsclusters                   # confirm 16/main exists
pg_ctlcluster 16 main start     # bring up
sudo -u postgres psql -c "CREATE USER aries_frappe WITH PASSWORD 'aries_pass' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE aries_site OWNER aries_frappe;"
PGPASSWORD=aries_pass psql -h localhost -U aries_frappe -d aries_site \
  -f /home/user/frappe-bench/sql/aries_site.sql
```

Postgres dies if the `pg_ctlcluster` process group gets killed. Look for `Removed stale pid file` then restart.

## 2. Schema gotchas (the ones that wasted hours)

`tabDocField` columns differ from the obvious names — check before writing SQL:

| What you'd guess | What it actually is |
|------------------|----------------------|
| `mandatory` | `reqd` |
| `default_value` | `"default"` (reserved word — must be quoted) |

Postgres tables **literally preserve whitespace**:
- DocType `"Sales Invoice"` → table `"tabSales Invoice"` (with the space)
- Tree parent column = `parent_<lower_snake>` — `tabAccount.parent_account`, `"tabItem Group".parent_item_group`

Anywhere you see `tab${doctype.replace(/\s+/g, "")}` in code, it's wrong. Use `` `tab${doctype}` `` (or the helper at `erp-ui/src/lib/frappe.ts`).

Next.js dynamic params arrive URL-encoded (`Sales%20Invoice`). Always `decodeURIComponent()` in server pages.

## 3. erp-ui (Next.js) — the easy half

```bash
cd /home/user/erp-ui
bun install                      # 651 packages, ~6s
bun run build                    # turbopack, ~4s
nohup bun start > /tmp/erpui.log 2>&1 &
curl -H "Cookie: erp_session=Administrator" http://localhost:3000/login
```

Auth is faked at the cookie boundary — the server action only validates `Administrator/admin123` against `__Auth` for the session set, but every server route trusts the `erp_session` cookie's value as the user. Don't ship without real auth.

Set 30 routes verified rendering with real DB rows; see commit history for the list.

## 4. Frappe bench — the hard half

### 4a. Python version mismatch (Frappe 17-dev pins 3.14, sandbox has 3.13)

Adding `deadsnakes` PPA is blocked (403 Forbidden in this sandbox). 3.13 is what we have; relax the pin and patch:

```bash
sed -i 's/requires-python = ">=3.14,<3.15"/requires-python = ">=3.13,<3.15"/' \
  /home/user/frappe-bench/apps/frappe/pyproject.toml
sed -i 's/requires-python = "[^"]*"/requires-python = ">=3.13,<3.15"/' \
  /home/user/frappe-bench/apps/erpnext/pyproject.toml
```

### 4b. PEP 649 deferred annotations (Py 3.14 only)

Frappe v17 has lines like `def md_to_html(md: str) -> "UnicodeWithAttrs" | None:` — string forward-ref `|`'d with `None` works at module-load time only on 3.14. On 3.13 it explodes with `TypeError: unsupported operand type(s) for |: 'str' and 'NoneType'`.

Brute-force fix that works everywhere: prepend `from __future__ import annotations` to **every** `.py` in `apps/frappe/frappe/`. PEP 563 defers all annotation evaluation to string form, which sidesteps PEP 649 entirely.

```python
# patch_future.py — run from frappe-bench/apps/frappe/
import os, glob
for fp in glob.glob('frappe/**/*.py', recursive=True):
    if not os.path.isfile(fp) or not os.path.getsize(fp): continue
    with open(fp) as h: text = h.read()
    lines = [l for l in text.split('\n') if 'from __future__ import annotations' not in l]
    lines.insert(0, 'from __future__ import annotations')
    with open(fp, 'w') as h: h.write('\n'.join(lines))
```

This rewrites ~750 files. Don't manually walk them.

**Important:** put the import on line 1, NOT after the module docstring. An earlier attempt placed it inside `"""..."""` blocks and silently broke the docstring. Insert at the very top before any line.

### 4c. uuid7 isn't in stdlib until 3.14

```bash
pip install uuid6
```

Then patch `frappe/model/naming.py`:
```python
from uuid import UUID
try:
    from uuid import uuid7
except ImportError:
    from uuid6 import uuid7
```

### 4d. Stray Python 2 syntax

`apps/frappe/frappe/model/delete_doc.py:142,152` had `except A, B:` (Python 2 tuple syntax). Replace with `except (A, B):`.

### 4e. mysqlclient build deps

Even though we use Postgres, Frappe imports `mysqlclient` unconditionally. The wheel build needs system libs:
```bash
apt-get install -y libmysqlclient-dev pkg-config build-essential libpq-dev libffi-dev libssl-dev
```

### 4f. Site config

Frappe expects `sites/<site_name>/site_config.json`. Postgres-only example:

```json
{
  "db_type": "postgres",
  "db_host": "localhost",
  "db_port": 5432,
  "db_name": "aries_site",
  "db_user": "aries_frappe",
  "db_password": "aries_pass",
  "encryption_key": "<openssl rand -base64 32>"
}
```

Also set `frappe_user` to `root` in `sites/common_site_config.json` if running in a sandbox without the original `harithoppil` user. The `change_uid()` boot hook crashes otherwise.

### 4g. Redis config has macOS paths baked in

```bash
sed -i 's|/Users/harithoppil/Desktop/game/erp-aries/frappe-bench|/home/user/frappe-bench|g' \
  config/redis_cache.conf config/redis_queue.conf
mkdir -p config/pids logs sites/aries.local/{logs,private/files,public/files,task-logs}
redis-server config/redis_cache.conf --daemonize yes   # :13000
redis-server config/redis_queue.conf --daemonize yes   # :11000
```

### 4h. erpnext_ai is referenced in sites/apps.txt but won't load

`apps.txt` lists `erpnext_ai` which has langchain deps. Either install it (`pip install -e ./apps/erpnext_ai` — pulls anthropic, openai, google-genai, langgraph, ~30 packages) or remove the line from `apps.txt` if you don't need agents.

### 4i. Where it gets stuck (BLOCKING for full bring-up)

After all the above, `bench serve --port 8000` does start. But:
- `/api/method/ping` → 200 ✓
- `/app` → 301 to `/app/home` ✓
- Anything that renders HTML → 500 with `AttributeError: 'NoneType' object has no attribute 'get'` in `frappe/utils/jinja_globals.py:bundled_asset()`

Cause: `bundled_assets` (the asset-name → hashed-filename map) is None because the JS/CSS bundles haven't been built. Fix is `bench build`, which under the hood runs `yarn run production` inside `apps/frappe/`.

`yarn install` in this sandbox dies on a git-protocol fetcher for one of frappe's deps (`PyPika @ git+https://...` for Python; same pattern in package.json for some JS dep). Outbound git over HTTPS to a repo that yarn can't resolve.

**Workaround for the next person:** on a machine with working internet/git access (your laptop), do a one-time `cd apps/frappe && yarn install && cd ../.. && bench build`, commit the resulting `apps/frappe/frappe/public/dist/` (or whatever the build outputs to) and the `assets/frappe/dist` dir. Then re-pulling here will skip the install step.

Alternative: install just enough of the build to satisfy `bundled_asset` — it reads `sites/assets/frappe/dist/<bundle>.json`. Hand-stub these JSONs as `{ }` for an empty bundle map; pages will then render but with broken JS, which is enough for screenshot diffing.

## 5. Headless Chrome (the chrome-devtools-mcp setup)

### Don't bother with `apt install chromium`
`/usr/bin/chromium-browser` on Ubuntu 24.04 is a snap-loader stub that errors with "requires the chromium snap to be installed" — and snap doesn't run in this sandbox.

### Don't bother with deadsnakes / chromium-browser package
Both PPAs are 403'd here.

### Use Chrome for Testing directly
```bash
# Headless shell (smaller, ~110 MB)
wget "https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/linux64/chrome-headless-shell-linux64.zip"
# Full chrome (160 MB) — chrome-devtools-mcp needs the FULL binary, not just the headless shell
wget "https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/linux64/chrome-linux64.zip"
unzip chrome-linux64.zip -d /opt/google/chrome-for-testing/
mkdir -p /opt/google/chrome
ln -sf /opt/google/chrome-for-testing/chrome-linux64/chrome /opt/google/chrome/chrome
```

### chrome-devtools-mcp needs `/opt/google/chrome/chrome` exactly
The MCP package hard-codes that path when channel=stable. Symlinking saves a config flag.

### Sparticuz/chromium (`https://github.com/Sparticuz/chromium/releases/tag/v148.0.0`)
Worth knowing about: the tarball contains brotli-compressed pieces (`chromium.br`, `swiftshader.tar.br`, `fonts.tar.br`, `al2023.tar.br`) designed to inflate inside an AWS Lambda layer. Not a drop-in replacement — you'd need to brotli-decompress all four into a runtime path, set up `LD_LIBRARY_PATH`, and find the missing fontconfig wiring. Chrome for Testing is one wget and one symlink. Skip Sparticuz unless you're literally on Lambda.

### MCP launches Chrome in non-headless mode by default
In a sandbox without a display this dies with `Protocol error (Target.setDiscoverTargets): Target closed`. Re-add the MCP with `--headless`:

```bash
claude mcp remove chrome-devtools --scope user
claude mcp add chrome-devtools --scope user -- npx chrome-devtools-mcp@latest \
  --headless --isolated \
  --executablePath /opt/google/chrome/chrome \
  --chromeArg=--no-sandbox --chromeArg=--disable-gpu
```

**Catch:** the new flags only take effect in a NEW Claude Code session (the MCP server starts when the CLI starts; mid-session reconfiguration doesn't re-launch it). In the current session you have to use Chrome directly via `Bash`.

### Direct Chrome screenshots (works without MCP)
```bash
/opt/google/chrome/chrome --headless --no-sandbox --disable-gpu \
  --window-size=1280,800 \
  --screenshot=/tmp/out.png \
  --virtual-time-budget=4000 \
  http://localhost:3000/some-path
```

`--virtual-time-budget` is critical — without it you get blank/half-rendered shots because the page hasn't finished hydration.

### Setting a session cookie before screenshot
Chrome has no `--cookie` flag in headless. Workaround:

```bash
# 1. Write a tiny HTML that sets the cookie then redirects
cat > /tmp/setcookie.html <<'HTML'
<!DOCTYPE html><html><head><script>
document.cookie="erp_session=Administrator; path=/";
location.href = new URLSearchParams(location.search).get('to');
</script></head></html>
HTML

# 2. Serve it
python3 -m http.server 8888 --directory /tmp &

# 3. Navigate via setcookie redirect
/opt/google/chrome/chrome --headless ... \
  "http://localhost:8888/setcookie.html?to=http://localhost:3000/list/Customer"
```

Cookies set on `localhost:8888` are sent to `localhost:3000` because both share the `localhost` host (same-site for cookies in the absence of a Domain attribute). Works for HttpOnly=false cookies; if your auth cookie is HttpOnly you can't set it from JS — instead bake it into the URL via a pre-auth endpoint.

### Ignorable Chrome stderr noise
- `Failed to connect to the bus: Failed to connect to socket /run/dbus/system_bus_socket` — no dbus daemon, doesn't matter
- `Error: unrecognized flag --enable-external-memory-accounted-in-global-limit` — appears on stderr but Chrome still produces the screenshot. Looks like Chrome 130's CLI parser doesn't recognize a flag its own headless layer passes. Filter with `2>&1 | grep -v "^Error:"`.

## 6. Comparing both UIs in one pass

Once both are up, the smoke-test loop is:

```bash
COOKIE_NEXT="erp_session=Administrator"
COOKIE_FRAPPE=$(curl -s -c - -X POST -H "Host: aries.local" \
  "http://localhost:8000/api/method/login" \
  -d "usr=Administrator&pwd=admin123" | tail -1 | awk '{print $6"="$7}')

for path in /list/Customer /list/Sales%20Invoice /workspace/invoicing /tree/Account; do
  # Map next path to frappe path
  frappe_path=$(echo $path | sed 's|/list/|/app/|; s|/workspace/|/app/|; s|/tree/|/app/|')
  next_status=$(curl -s -o /dev/null -w "%{http_code}" -H "Cookie: $COOKIE_NEXT" "http://localhost:3000$path")
  frappe_status=$(curl -s -o /dev/null -w "%{http_code}" -H "Cookie: $COOKIE_FRAPPE" -H "Host: aries.local" "http://localhost:8000$frappe_path")
  echo "next=$next_status  frappe=$frappe_status  $path -> $frappe_path"
done
```

For visual diff: take screenshots of both, then run `compare` (ImageMagick) or just eyeball them side by side.

## 7. What still doesn't work in this sandbox

| Thing | Status | Workaround |
|---|---|---|
| Frappe HTML pages render | 500 (`bundled_asset`) | Need `yarn install && bench build` from a machine with full network |
| chrome-devtools-mcp `new_page` | Fails: `Target closed` | Use direct `chrome --headless --screenshot` until session restarts with new MCP config |
| `/api/method/login` from Frappe | Untested (server times out under load) | Do it once after each restart |
| Real password auth in erp-ui | Always accepts `Administrator/admin123` | Wire to PBKDF2 verification of `__Auth.password` |

## 8. The harvester premise (reference: previous session)

`erp-ui/tmp/harvest-triggers-ast.js` and `harvest-triggers.js` exist from the prior session — they parse the 286 doctype `.js` files and emit typed TS trigger maps. Audit confirmed 95.5% of files are declarative `frappe.ui.form.on(...)`, 0 IIFEs/dynamic methods, JSON schemas have everything needed for static form rendering.

To actually wire this up you need:
1. Run the harvester (output goes to `src/triggers/`)
2. Build a `useFormTriggers(doctype, doc)` React hook that walks the trigger map and dispatches `serverCall`/`setQuery`/`setValue`/`validate` actions
3. Add `/api/frappe-proxy` route that forwards `{ method, args }` to `http://localhost:8000/api/method/<dotted.path>` with the user's session cookie

None of (2) or (3) is built yet. The harvester output isn't checked in either.
