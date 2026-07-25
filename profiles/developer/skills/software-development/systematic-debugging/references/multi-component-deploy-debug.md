# Multi-Component Deployment Debugging

## JSON Structure Reconciliation

**Symptom:** API endpoint returns 200 but zero items, or frontend renders empty lists/blanks.

**Root cause pattern:** JSON data files use one key name (e.g. `sql_questions`, `livecoding_tasks`),
but consuming code expects another (e.g. `questions`, `live_coding`).

**Fix workflow:**
1. `curl` the API endpoint, save raw response
2. Check top-level keys in the JSON: `python3 -c "import json; d=json.load(open('file.json')); print([k for k in d if k!='meta'])"`
3. Compare each key against the code's `bank.get("expected_key", [])`
4. Fix BOTH backend AND frontend — they often have the same mismatch
5. For field-level mismatches (e.g. `task` vs `question` vs `description`), add fallback chain: `t.question || t.task || t.description`

**Common JSON key patterns seen:**
- `sql_questions` / `theory_questions` / `api_test_cases` (not `questions`)
- `livecoding_tasks` / `autotest_project` (not `live_coding`)
- `task` / `solution` (not `question` / `answer`)

## Native Fallback When Docker Is Unavailable

**When:** `docker compose up` fails (daemon not running, macOS vmnetd issues, OOM kills).

**Checklist — run services natively:**

1. **PostgreSQL:** check if already running (`pg_isready`), find correct instance (`ps aux | grep postgres`). Multiple PG versions may coexist — use the running one, not the one you expected.
2. **pg_hba.conf:** may need `trust` instead of `scram-sha-256` for local dev. Backup first, then: `sudo sed -i '' 's/scram-sha-256/trust/g' /path/to/pg_hba.conf && pg_ctl reload`
3. **Create DB/user:** `CREATE USER ... WITH PASSWORD`, `CREATE DATABASE ... OWNER`, `GRANT USAGE ON SCHEMA`
4. **Apply SQL:** `psql -h 127.0.0.1 -U user -d db -f schema.sql`
6. **Backend env vars:** DB_HOST=localhost (not container name), DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
7. **Schema search_path:** if tables live in `ecommerce`/`banking` schemas (not `public`), the backend must run `SET search_path TO ecommerce, banking, public` before each query — otherwise `relation "client" does not exist`. Also: `GRANT USAGE ON SCHEMA ... TO user`.
8. **Mock API:** if original uses WireMock/Docker, write a quick Python FastAPI mock — same endpoints, same CORS
9. **Frontend:** `npm install` (if it hangs >2min, kill and retry with `--prefer-offline`). If `node` not found in non-interactive shell, source nvm: `export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"`. Then `npx vite --host 0.0.0.0 --port 3000` with VITE_API_URL and VITE_MOCK_URL env vars.

## Screenshot-Driven Verification (OCR)

**When:** user provides reference screenshots of expected UI/schema/API format.

**Workflow:**
1. Check if `tesseract` is available: `which tesseract`
2. Serve images via `python3 -m http.server 9999` for browser access
3. OCR: `tesseract image.jpg stdout -l rus+eng`
4. Compare extracted structure (table names, columns, field names, flow steps) against actual code
5. Fix mismatches — screenshots are the spec

**Common mismatches caught this way:**
- API field names (`fromAccount` vs `source_account_id`)
- Missing DB schema display in UI
- Architecture flow step differences
