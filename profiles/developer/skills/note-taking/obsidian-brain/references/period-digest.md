# Period digest — rebuilding «what did we do» from evidence

Recipe for a day/week/month summary note in the vault.

## 1. Discover repos and their commits

Run this inside `execute_code` (Python), NOT as one broad `terminal` command: a `find` over `$HOME` piped into a git loop can trip the terminal approval gate and hang the session, while the same work in Python returns instantly.

```python
import glob, subprocess
repos = set()
for base in ["~/projects", "~/trainer", "~/IdeaProjects", "~/portfolio", "~/Odsidian/obsidians"]:
    for g in glob.glob(f"{base}/**/.git", recursive=True):
        repos.add(g[:-4])
for r in sorted(repos):
    out = subprocess.run(["git", "-C", r, "log", "--since=2026-09-14",
                          "--date=format:%m-%d %H:%M", "--pretty=%ad %h %s"],
                         capture_output=True, text=True).stdout
    print("===", r, len([l for l in out.splitlines() if l.strip()]), "commits")
    print(out[:3000])
```

Trim the base list to the dirs that actually hold work (`~/projects`, `~/trainer`, the vault repo); `glob(**)` also walks large trees.

## 2. Hermes session evidence

One `state.db` per profile: `~/.hermes/profiles/<profile>/state.db` (plus `~/.hermes/state.db` for the default profile). Open read-only while the agent is running:

```python
con = sqlite3.connect("file:/Users/<user>/.hermes/profiles/developer/state.db?mode=ro", uri=True)
```

Relevant tables:

- `sessions(id, source, user_id, model, started_at, ended_at, end_reason, message_count, tool_call_count, input_tokens, output_tokens)` — `started_at`/`ended_at` are epoch-seconds timestamps (filter with `time.mktime(time.strptime("YYYY-MM-DD", "%Y-%m-%d"))`, print with `datetime.fromtimestamp`).
- `messages(id, session_id, role, content, tool_name, timestamp, token_count)` — first user message per session gives the topic when the commit log alone is thin.
- `session_model_usage(session_id, model, api_call_count, input_tokens, output_tokens, estimated_cost_usd, ...)` — for cost/token tables.
- `kanban.db`, `projects.db` exist but are usually empty here — don't build a summary on them.

Per-day rollup that reads well in the note: sessions / messages / tool-calls / input tokens / output tokens per `date(started_at)`.

## 3. Vault-side evidence

- Files touched in the window: walk the vault with `os.walk` and compare `st_mtime` (a `find ... -newermt` over the vault works too, but keep it inside `execute_code`).
- The vault's own history: `git -C "/Users/<user>/Odsidian/obsidians" log --since=... --stat` — the repo also ships the bot-written notes (`04 Notes/Voice`, `04 Notes/Links`, `02 Tasks`, `01 Topics`).
- `Brain/journal/YYYY-MM-DD.md` shows whether the day already has a dev-journal entry; missing days are the ones to create.

## 4. Where the note goes

- Period digest: `Brain/notes/weekly/<from>--<to>.md` (create the dir; the vault had no weekly convention before this, keep the `YYYY-MM-DD--YYYY-MM-DD` name so windows sort).
- Dev journal: `Brain/journal/YYYY-MM-DD.md`, header `# Dev Journal — YYYY-MM-DD`, one line per event:
  `HH:MM | project:<project> | <what happened> — commit <sha>` (project name matches the repo/dir name).
- Footer style used across `Brain/notes/`: a closing block with `tags: [...]`, `created:`, and (for digests) `period:`.
- Wikilink related notes (`[[agency-agents-guide    AGENTS АГЕНТЫ]]`, `[[summary]]`, topic notes) — filenames with spaces work as wikilinks as-is.

## 5. Publish

```bash
cd "/Users/<user>/Odsidian/obsidians"
git add -A
python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged   # exit 0 + no output = clean
git commit -m "Brain: итоги недели <from>-<to> + dev journal"
git push
```

The scanner prints findings on stderr and returns 1; a silent run with `exit_code 0` means clean.

## 6. Honesty rules

- `vibecode_tracker.py stats week` is secondary evidence: it only counts logged segments, so a heavy week with no `segment` calls reads as minutes. Quote it with the caveat (or backfill first — see the `vibecode-tracker` skill).
- If a day has no commits and no sessions, say so; do not invent activity from neighbouring days.
