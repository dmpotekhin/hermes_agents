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
- Long single-shot sessions (one big feature, no intermediate segment calls) are the common case that triggers this: the whole working window gets classified as a pause. Proven backfill on 2026-09-18 (34m lost): in `state["current"]` move the pause entry into `segments` as `{"from": <pause.from>, "to": <pause.to>, "duration_seconds": <gap_seconds>, "project": "<project>"}`, clear `pauses`, set `commits` to the real count, then run `stop` — it appends the tail (≤10 min) as a second real segment and writes the daily log. Defense: call `segment <project>` intermediiately after each commit **and** after a long verification pass, not only once at the end.
- `stats` counts SEGMENTS as «Коммитов» (a session with 1 commit + a wrap-up segment shows `Коммитов: 2`), while `stop` prints `commits` from the state field. Not a bug to hunt — just don't be surprised by the mismatch.
- `stats today` includes the live session (fixed 2026-08-16: previously it only read completed `sessions`, so the daily log and CLI stats disagreed). If stats ever shows less than the daily log, check `state["current"]` is being appended.
- `_write_daily_log(date_str, state, completed_session)` — argument order matters: first arg is the date string, second is state dict.
