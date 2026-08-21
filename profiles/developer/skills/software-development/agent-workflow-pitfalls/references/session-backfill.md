# Session Data Backfill: Reconstruct History from Git + Sessions

How to rebuild historical coding-time data when no live tracker existed.

## Data Sources (pick what's available)

1. **Session history** — `session_search()` returns `started_at`, `last_active`, `message_count`
2. **Profile session DBs** — SQLite at `~/.hermes/profiles/<name>/state.db`, table `sessions`
3. **Git commits** — `git log --since=<date> --format="%aI|%s"` from all project repos

## Estimation Rules

| Session type | Estimation | Cap |
|-------------|-----------|-----|
| Coding (has commits that day) | span(first_commit, last_commit) + 30min buffer | 5h |
| Single-commit day | 5 min minimum | — |
| Planning (messages, no commits) | msg_count × 30s | 2h |
| Learning (japanese-tutor style) | wall_clock × 0.55 | 2h |

## Process

1. Collect all sessions + commits, group by date
2. Estimate active time per day using rules above
3. Write daily logs to Obsidian vault with backfill disclaimer
4. Add `<!-- LIVE -->` marker to protect from future live-tracker overwrites
5. Rebuild summary.md from daily logs (monthly + per-project breakdown)

## Per-project timing

Daily totals split across projects is unreliable (one day = multiple projects).
Use session-level estimates for per-project breakdown:

```python
for date, project, seconds in session_estimates:
    all_projects[project]["total"] += seconds
```

NOT:
```python
# Wrong: divides daily total evenly across all projects
daily_total / len(day_projects)
```

## Verification

After backfill:
- Every daily log must have `<!-- LIVE -->` marker
- Run live tracker's `segment` → verify backfill section unchanged
- Run live tracker's `stop` → verify summary NOT overwritten
