#!/usr/bin/env python3
"""Vibecode time tracker — tracks coding sessions with Hermes.
Usage:
  vibecode_tracker.py start [project]   — begin session (or resume after pause)
  vibecode_tracker.py segment [project] — log a commit/push segment
  vibecode_tracker.py stop              — end session
  vibecode_tracker.py stats [today|week|month|all]  — show statistics
  vibecode_tracker.py status            — show current session status
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
PROFILE = os.environ.get("HERMES_PROFILE", "developer")
# HERMES_HOME may already point to a profile dir (e.g. ~/.hermes/profiles/developer).
# Detect: if basename is not "hermes", it's a profile dir — state goes under it.
# Otherwise construct the full profiles/<name>/state path.
if HERMES_HOME.name == "hermes":
    STATE_DIR = HERMES_HOME / "profiles" / PROFILE / "state"
else:
    STATE_DIR = HERMES_HOME / "state"
STATE_FILE = STATE_DIR / "vibecode_state.json"
OBSIDIAN_VAULT = Path(os.path.expanduser(
    "~/Odsidian/obsidians/Obsidian Vault/Brain/notes/vibecoding"
))

NOW = datetime.now()
TODAY = NOW.strftime("%Y-%m-%d")


def ensure_dirs():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_VAULT.mkdir(parents=True, exist_ok=True)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"sessions": [], "current": None}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def fmt_duration(seconds):
    if seconds < 60:
        return f"{int(seconds)}с"
    mins = int(seconds / 60)
    if mins < 60:
        return f"{mins}м"
    h = mins // 60
    m = mins % 60
    return f"{h}ч {m}м"


def parse_iso(ts_str):
    return datetime.fromisoformat(ts_str)


def daily_log_path(date_str):
    return OBSIDIAN_VAULT / f"{date_str}.md"


def summary_path():
    return OBSIDIAN_VAULT / "summary.md"


def cmd_start(project="unknown"):
    state = load_state()
    now_iso = NOW.isoformat()

    if state["current"]:
        # Already running — log a pause gap if > 5 min
        last = parse_iso(state["current"]["last_segment"])
        gap = (NOW - last).total_seconds()
        if gap > 300:
            state["current"]["pauses"].append({
                "from": state["current"]["last_segment"],
                "to": now_iso,
                "gap_seconds": int(gap)
            })

    state["current"] = {
        "started": now_iso,
        "last_segment": now_iso,
        "project": project,
        "segments": [],
        "pauses": [],
        "commits": 0
    }
    save_state(state)

    rel_path = daily_log_path(TODAY).relative_to(
        Path(os.path.expanduser("~/Odsidian/obsidians/Obsidian Vault"))
    )
    print(f"▶ Сессия начата: {NOW.strftime('%H:%M')} ({project})")
    print(f"  Лог: Brain/notes/vibecoding/{TODAY}.md")


def cmd_segment(project=None):
    state = load_state()
    if not state["current"]:
        print("⚠ Нет активной сессии. Используй 'start' сначала.")
        sys.exit(1)

    now_iso = NOW.isoformat()
    last = parse_iso(state["current"]["last_segment"])
    gap = (NOW - last).total_seconds()

    # Auto-pause: if idle > 10 min, don't count the gap as active time
    if gap > 600:
        state["current"]["pauses"].append({
            "from": state["current"]["last_segment"],
            "to": now_iso,
            "gap_seconds": int(gap)
        })
        state["current"]["last_segment"] = now_iso
        state["current"]["project"] = project or state["current"]["project"]
        save_state(state)
        print(f"⏸ Пауза: {fmt_duration(gap)} (авто, простой >10 мин)")
        print(f"▶ Отсчёт активного времени сброшен")
        return

    segment = {
        "from": state["current"]["last_segment"],
        "to": now_iso,
        "duration_seconds": int(gap),
        "project": project or state["current"]["project"]
    }
    state["current"]["segments"].append(segment)
    state["current"]["commits"] += 1
    state["current"]["last_segment"] = now_iso
    if project:
        state["current"]["project"] = project
    save_state(state)

    print(f"📝 Сегмент: {fmt_duration(gap)} ({segment['project']})")
    _update_daily_log(state, TODAY)


def cmd_stop():
    state = load_state()
    if not state["current"]:
        print("⚠ Нет активной сессии.")
        sys.exit(1)

    # Log final segment
    last = parse_iso(state["current"]["last_segment"])
    duration = (NOW - last).total_seconds()
    if duration > 30:  # only log if > 30 sec
        state["current"]["segments"].append({
            "from": state["current"]["last_segment"],
            "to": NOW.isoformat(),
            "duration_seconds": int(duration),
            "project": state["current"]["project"]
        })

    state["current"]["ended"] = NOW.isoformat()
    total = sum(s["duration_seconds"] for s in state["current"]["segments"])
    pauses = sum(p["gap_seconds"] for p in state["current"]["pauses"])

    # Move to history
    state["sessions"].append(state["current"])
    state["current"] = None
    save_state(state)

    print(f"■ Сессия завершена: {fmt_duration(total)} активно")
    if pauses:
        print(f"  Пауз: {fmt_duration(pauses)}")
    print(f"  Коммитов: {state['sessions'][-1]['commits']}")
    _update_daily_log_for_session(state["sessions"][-1], TODAY)
    _update_summary(state, TODAY)


def cmd_status():
    state = load_state()
    if not state["current"]:
        print("○ Нет активной сессии.")
        return

    cur = state["current"]
    started = parse_iso(cur["started"])
    elapsed = (NOW - started).total_seconds()
    total_active = sum(s["duration_seconds"] for s in cur["segments"])
    last_seg = (NOW - parse_iso(cur["last_segment"])).total_seconds()

    print(f"● Активна с: {started.strftime('%H:%M')} ({fmt_duration(elapsed)} назад)")
    print(f"  Проект: {cur['project']}")
    print(f"  Сегментов: {len(cur['segments'])}")
    print(f"  Активно: {fmt_duration(total_active)}")
    print(f"  Коммитов: {cur['commits']}")
    print(f"  С последнего сегмента: {fmt_duration(last_seg)}")


def cmd_stats(period="today"):
    state = load_state()
    all_sessions = state.get("sessions", [])

    if period == "today":
        sessions = [s for s in all_sessions
                    if parse_iso(s["started"]).strftime("%Y-%m-%d") == TODAY]
    elif period == "week":
        week_ago = NOW - timedelta(days=7)
        sessions = [s for s in all_sessions
                    if parse_iso(s["started"]) >= week_ago]
    elif period == "month":
        month_start = NOW.strftime("%Y-%m")
        sessions = [s for s in all_sessions
                    if parse_iso(s["started"]).strftime("%Y-%m") == month_start]
    else:
        sessions = all_sessions

    if not sessions:
        print(f"Нет данных за период: {period}")
        return

    total = 0
    total_commits = 0
    projects = set()

    print(f"\n{'='*50}")
    print(f"  Вайбкодинг — {period}")
    print(f"{'='*50}")
    print(f"  {'Дата':<12} {'Время':>8}  {'Коммитов':>8}  Проекты")
    print(f"  {'-'*12} {'-'*8}  {'-'*8}  {'-'*20}")

    for s in sessions:
        d = parse_iso(s["started"]).strftime("%d %b")
        dur = sum(seg["duration_seconds"] for seg in s["segments"])
        commits = sum(1 for seg in s["segments"])
        projs = set(seg["project"] for seg in s["segments"])
        total += dur
        total_commits += commits
        projects.update(projs)
        print(f"  {d:<12} {fmt_duration(dur):>8}  {commits:>8}  {', '.join(sorted(projs))}")

    print(f"  {'─'*50}")
    print(f"  Всего: {fmt_duration(total)} | Коммитов: {total_commits} | Проектов: {len(projects)}")
    print(f"{'='*50}\n")


def _update_daily_log(state, date_str):
    """Update daily log with current session segments."""
    cur = state["current"]
    if not cur:
        return
    _write_daily_log(date_str, state)


def _update_daily_log_for_session(session, date_str):
    """Update daily log for a completed session."""
    _write_daily_log(date_str, None, completed_session=session)


def _write_daily_log(date_str, state=None, completed_session=None):
    path = daily_log_path(date_str)

    # Collect segments from all sessions for this date
    all_segments = []

    if state:
        sessions = state.get("sessions", [])
        for s in sessions:
            s_date = parse_iso(s["started"]).strftime("%Y-%m-%d")
            if s_date == date_str:
                for i, seg in enumerate(s["segments"]):
                    all_segments.append((s, seg, i))
        # Also include current (active) session segments
        cur = state.get("current")
        if cur:
            cur_date = parse_iso(cur["started"]).strftime("%Y-%m-%d")
            if cur_date == date_str:
                for i, seg in enumerate(cur["segments"]):
                    all_segments.append((cur, seg, i))

    if completed_session:
        s = completed_session
        s_date = parse_iso(s["started"]).strftime("%Y-%m-%d")
        if s_date == date_str:
            for i, seg in enumerate(s["segments"]):
                all_segments.append((s, seg, i))

    if not all_segments:
        return

    total = sum(seg["duration_seconds"] for _, seg, _ in all_segments)
    total_commits = len(all_segments)
    projects = set(seg["project"] for _, seg, _ in all_segments)

    lines = []
    lines.append(f"# Вайбкодинг — {date_str}\n")
    lines.append(f"| # | Начало | Длит. | Проект |")
    lines.append(f"|---|--------|-------|--------|")

    for i, (sess, seg, _) in enumerate(all_segments, 1):
        start = parse_iso(seg["from"]).strftime("%H:%M")
        dur = fmt_duration(seg["duration_seconds"])
        proj = seg["project"]
        lines.append(f"| {i} | {start} | {dur} | {proj} |")

    lines.append("")
    lines.append(f"**Всего за день: {fmt_duration(total)}** | **Сегментов: {total_commits}** | **Проектов: {len(projects)}**")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _update_summary(state, date_str):
    """Update summary statistics."""
    path = summary_path()
    all_sessions = state.get("sessions", [])

    if not all_sessions:
        return

    # Group by month
    months = {}
    for s in all_sessions:
        month = parse_iso(s["started"]).strftime("%Y-%m")
        if month not in months:
            months[month] = {"total_seconds": 0, "commits": 0, "projects": set(), "days": set()}
        dur = sum(seg["duration_seconds"] for seg in s["segments"])
        months[month]["total_seconds"] += dur
        months[month]["commits"] += sum(1 for _ in s["segments"])
        months[month]["projects"].update(seg["project"] for seg in s["segments"])
        months[month]["days"].add(parse_iso(s["started"]).strftime("%Y-%m-%d"))

    grand_total = sum(m["total_seconds"] for m in months.values())
    grand_commits = sum(m["commits"] for m in months.values())

    lines = []
    lines.append("# Вайбкодинг — статистика\n")
    lines.append("> Автоматический трекинг времени в Hermes\n")
    lines.append(f"| Месяц | Дней | Время | Коммитов | Проектов |")
    lines.append(f"|-------|------|-------|----------|----------|")

    for month in sorted(months.keys()):
        m = months[month]
        lines.append(
            f"| {month} | {len(m['days'])} | {fmt_duration(m['total_seconds'])} "
            f"| {m['commits']} | {len(m['projects'])} |"
        )

    lines.append("")
    lines.append(f"**Всего за всё время: {fmt_duration(grand_total)}** | **Коммитов: {grand_commits}**")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    ensure_dirs()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    extra = sys.argv[2] if len(sys.argv) > 2 else None

    if cmd == "start":
        cmd_start(extra or "unknown")
    elif cmd == "segment":
        cmd_segment(extra)
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "status":
        cmd_status()
    elif cmd == "stats":
        cmd_stats(extra or "today")
    else:
        print(f"Неизвестная команда: {cmd}")
        print(__doc__)
        sys.exit(1)
