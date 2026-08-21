---
name: vibecode-tracker
description: Track vibe coding time. Log segments, show stats.
version: 1.1.0
---

# Vibecode Time Tracker

Track time spent vibe coding with Hermes across ALL profiles. Auto-detects profile from HERMES_HOME.

## Global tracker

```bash
python3 ~/.hermes/scripts/vibecode_tracker.py start [project]
python3 ~/.hermes/scripts/vibecode_tracker.py segment [project]
python3 ~/.hermes/scripts/vibecode_tracker.py stop
python3 ~/.hermes/scripts/vibecode_tracker.py status
python3 ~/.hermes/scripts/vibecode_tracker.py stats [today|week|month|all]
```

State: `~/.hermes/state/vibecode_state.json` (shared across all profiles).

## Workflow

1. Agent calls `start` at session beginning
2. Agent calls `segment <project>` after each commit/push
3. User asks "сколько я кодил" → agent calls `stats`
4. Agent calls `stop` when conversation ends

## Obsidian output

- Daily: `Brain/notes/vibecoding/YYYY-MM-DD.md` (grouped by profile)
- Summary: `Brain/notes/vibecoding/summary.md` (monthly stats)

## Auto-pause

If >10 min pass between segments, gap is logged as pause (not counted). Timer resets.

## Pitfalls

- Auto-pause threshold: 10 minutes
- Midnight sessions split across two daily files
- State file: `~/.hermes/state/vibecode_state.json`
- `segment` after >10 min idle does NOT count time — it logs a pause and resets the timer. If a session ran but no segment was logged in time, backfill manually: edit state JSON (turn `pauses` into a real `segments` entry) or accept the gap as idle.
- `stats today` includes the live session (fixed 2026-08-16: previously it only read completed `sessions`, so the daily log and CLI stats disagreed). If stats ever shows less than the daily log, check `state["current"]` is being appended.
- `_write_daily_log(date_str, state, completed_session)` — argument order matters: first arg is the date string, second is state dict.
