# QA Interview Trainer — Session Fix Log

## Backend fixes (main.py)

### 1. JSON key mismatches
Each JSON data file used a different top-level key for questions. The code assumed `bank.get("questions", [])`, but:
- `sql_question_bank.json` → key is `sql_questions`
- `java_trainer_bank.json` → key is `livecoding_tasks`
- `java_core_questions.json` → key is `questions` ✓
- `qa_questions.json` → key is `questions` ✓

**Fix**: update each endpoint's load logic to use the actual key name.

### 2. Schema search_path
Tables live in `ecommerce` and `banking` schemas, not `public`. User queries without schema prefix fail.

**Fix**: add `cur.execute("SET search_path TO ecommerce, banking, public")` before every user/reference SQL execution in `run_sql()`.

### 3. Missing schema GRANTs
After creating the `trainer` user, tables in non-public schemas weren't accessible.

**Fix**:
```sql
GRANT USAGE ON SCHEMA ecommerce, banking TO trainer;
GRANT SELECT ON ALL TABLES IN SCHEMA ecommerce, banking TO trainer;
```

## Frontend fixes

### 1. SqlTrainer.jsx — question list key
```js
// Before:
const items = Array.isArray(d) ? d : (d.questions || [])
// After:
const items = Array.isArray(d) ? d : (d.sql_questions || d.questions || [])
```

### 2. JavaTrainer.jsx — task list key and description field
```js
// Before:
const tasks = data.live_coding || data.tasks || ...
<p>{t.question || t.description}</p>
// After:
const tasks = data.livecoding_tasks || data.live_coding || data.tasks || ...
<p>{t.question || t.task || t.description}</p>
```

### 3. ApiCases.jsx — request body fields
Screenshot showed `source_account_id`/`destination_account_id` (UUIDs), but frontend sent `fromAccount`/`toAccount` (short strings).

**Fix**: use UUIDs matching the screenshot format, add `description` field, fix auth header.

### 4. ApiCases.jsx — broken string literal
`'Bearer ***` (password-masked in terminal output) produced broken JS. Always verify the actual file content after `patch` with `read_file`.

## SQL trainer enrichments added

### DB Schema panel
Collapsible sidebar section showing both schemas (ECOMMERCE + BANKING) with table names, columns, types, and PK/FK/UK markers.

### Hint format (22 questions rewritten)
Each hint now follows a structured format:
- 🟢 ТАБЛИЦЫ — which tables, with PK/FK
- 🔗 СВЯЗИ — JOIN conditions, relationship types
- 💡 ПОДХОД — step-by-step logic
- 🐞 БАГ-ХАНТИНГ — which seeded bug to find (where applicable)
- ⚠️ ОШИБКИ — common mistakes

### Reference answer display
After clicking "Проверить", a collapsible "✅ Эталонный ответ" block appears showing the correct SQL in a dark-themed code block. Uses `current.answer` from the question bank JSON.

## Project startup script (start.sh)

Created `start.sh` at project root for one-command restart:

- Kills any processes on target ports (8000, 8080, 3000) before starting
- Sources nvm for Node.js in non-interactive shell
- Exports DB_* env vars (DB_HOST=localhost overrides Docker default)
- Starts backend, mock API, frontend as background nohup processes
- Logs go to /tmp/trainer-{backend,mock,frontend}.log
- Runs 3-second health checks after startup
- Prints ready message with all URLs

Template available at `templates/start-native.sh` in this skill.

## GitHub push notes

### SSH auth
`ssh -T git@github.com` confirms SSH key works. Use `git@github.com:user/repo.git` as remote when HTTPS token is unavailable.

### Merge unrelated histories
When GitHub auto-creates `master` with a default README but the project was initialized locally on `main`:
```bash
git checkout -b master origin/master
git merge main --allow-unrelated-histories
# Resolve conflicts: keep project files
git checkout --theirs README.md .gitignore
git add -A && git commit -m "Merge main into master"
git push origin master
```

### Screenshot OCR verification
When reference screenshots need to be compared against actual code:
```bash
# Serve images for browser + OCR
python3 -m http.server 9999 &
tesseract telegram-cloud-photo-*.jpg stdout -l rus+eng
```
Extract table schemas, field names, flow steps from OCR output; compare against code.
