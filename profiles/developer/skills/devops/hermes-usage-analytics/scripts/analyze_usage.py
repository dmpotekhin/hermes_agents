#!/usr/bin/env python3
"""Hermes token/cost analytics across all profiles.

Usage:
  python3 analyze_usage.py                     # per-profile totals + per-model + per-month
  python3 analyze_usage.py --breakdown NAME    # deep-dive one profile (developer, etc.)

Reads ONLY from ~/.hermes/state.db and ~/.hermes/profiles/<name>/state.db (read-only URI).
Requires Python 3.8+. No third-party deps (stdlib sqlite3).
"""
import sqlite3, os, sys
from datetime import datetime

HOME = os.path.expanduser("~")

def discover_profiles():
    """Return {name: db_path_or_None} for default + all profile dirs."""
    prof = {"default": os.path.join(HOME, ".hermes", "state.db")}
    pdir = os.path.join(HOME, ".hermes", "profiles")
    if os.path.isdir(pdir):
        for name in sorted(os.listdir(pdir)):
            if name.startswith("."):
                continue
            prof[name] = os.path.join(pdir, name, "state.db")
    return prof

def q(db, sql, args=()):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()

def ts(epoch):
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d") if epoch else "?"

def profile_summary(name, db):
    if not os.path.exists(db):
        return None
    r = q(db, """
        SELECT COUNT(*) n, COALESCE(SUM(input_tokens),0) inp,
               COALESCE(SUM(output_tokens),0) out,
               COALESCE(SUM(cache_read_tokens),0) cr,
               COALESCE(SUM(cache_write_tokens),0) cw,
               COALESCE(SUM(reasoning_tokens),0) rs,
               COALESCE(SUM(estimated_cost_usd),0) est,
               COALESCE(SUM(api_call_count),0) api,
               COALESCE(SUM(tool_call_count),0) tools,
               MIN(started_at) first_s, MAX(started_at) last_s
        FROM sessions
    """)[0]
    return {
        "n": r["n"], "inp": r["inp"], "out": r["out"], "cr": r["cr"], "cw": r["cw"],
        "rs": r["rs"], "est": r["est"], "api": r["api"], "tools": r["tools"],
        "first": ts(r["first_s"]), "last": ts(r["last_s"]),
    }

def breakdown(db, name):
    print(f"\n=== {name.upper()} — ПО ДНЯМ ===")
    ti = to = tc = te = 0
    for r in q(db, """
        SELECT date(started_at,'unixepoch') d, COUNT(*) n, SUM(input_tokens) inp,
               SUM(output_tokens) out, SUM(cache_read_tokens) cr, SUM(reasoning_tokens) rs,
               SUM(estimated_cost_usd) est, SUM(api_call_count) api, SUM(tool_call_count) tools
        FROM sessions GROUP BY d ORDER BY d
    """):
        ti += r["inp"] or 0; to += r["out"] or 0; tc += r["cr"] or 0; te += r["est"] or 0
        print(f"{r['d']}  sess={r['n']:>3}  inp={r['inp'] or 0:>9,}  out={r['out'] or 0:>9,}  cr={r['cr'] or 0:>12,}  rs={r['rs'] or 0:>8,}  api={r['api'] or 0:>4}  tools={r['tools'] or 0:>4}  ${r['est'] or 0:>7.2f}")
    print(f"ИТОГО  inp={ti:,} out={to:,} cr={tc:,} est=${te:.2f}")

    print(f"\n=== {name.upper()} — ПО ИСТОЧНИКАМ ===")
    for r in q(db, """
        SELECT source, COUNT(*) n, SUM(input_tokens) inp, SUM(output_tokens) out,
               SUM(cache_read_tokens) cr, SUM(estimated_cost_usd) est,
               SUM(api_call_count) api, SUM(tool_call_count) tools
        FROM sessions GROUP BY source ORDER BY est DESC
    """):
        print(f"{r['source']:<12} sess={r['n']:>3}  inp={r['inp'] or 0:>9,}  out={r['out'] or 0:>9,}  cr={r['cr'] or 0:>12,}  api={r['api'] or 0:>4}  tools={r['tools'] or 0:>4}  ${r['est'] or 0:>7.2f}")

    print(f"\n=== {name.upper()} — ПО МОДЕЛЯМ (сессии) ===")
    for r in q(db, """
        SELECT COALESCE(model,'?') model, COUNT(*) n, SUM(input_tokens) inp,
               SUM(output_tokens) out, SUM(cache_read_tokens) cr, SUM(reasoning_tokens) rs,
               SUM(estimated_cost_usd) est, SUM(api_call_count) api, SUM(tool_call_count) tools
        FROM sessions GROUP BY model ORDER BY est DESC
    """):
        print(f"{r['model']:<28} sess={r['n']:>3}  inp={r['inp'] or 0:>9,}  out={r['out'] or 0:>9,}  cr={r['cr'] or 0:>12,}  rs={r['rs'] or 0:>8,}  api={r['api'] or 0:>4}  tools={r['tools'] or 0:>4}  ${r['est'] or 0:>7.2f}")

    print(f"\n=== {name.upper()} — ТОП-15 СЕССИЙ ПО СТОИМОСТИ ===")
    for r in q(db, """
        SELECT date(started_at,'unixepoch') d, COALESCE(model,'?') model,
               COALESCE(source,'?') source, COALESCE(title,'(без названия)') title,
               input_tokens inp, output_tokens out, cache_read_tokens cr, reasoning_tokens rs,
               estimated_cost_usd est, api_call_count api, tool_call_count tools, message_count msg
        FROM sessions ORDER BY est DESC LIMIT 15
    """):
        t = (r["title"] or "(без названия)")[:45]
        print(f"{r['d']} {r['model']:<22} src={r['source']:<5} est=${r['est'] or 0:>6.2f} cr={r['cr'] or 0:>10,} inp={r['inp'] or 0:>8,} out={r['out'] or 0:>8,} tools={r['tools'] or 0:>3} msg={r['msg'] or 0:>3} | {t}")

    print(f"\n=== {name.upper()} — БАКЕТЫ (длина сессии / tool-calls / длительность) ===")
    for label, expr in [
        ("messages", "message_count"),
        ("tools", "tool_call_count"),
    ]:
        print(f"{label}:")
        for r in q(db, f"""
            SELECT CASE WHEN {expr} <= 10 THEN '0-10'
                        WHEN {expr} <= 50 THEN '11-50'
                        WHEN {expr} <= 200 THEN '51-200'
                        ELSE '200+' END b,
                   COUNT(*) n, SUM(estimated_cost_usd) est
            FROM sessions GROUP BY b ORDER BY MIN({expr})
        """):
            print(f"  {r['b']:<8} sess={r['n']:>3}  est=${r['est'] or 0:>7.2f}")
    print("duration:")
    for r in q(db, """
        SELECT CASE WHEN (ended_at-started_at) < 900 THEN '<15m'
                    WHEN (ended_at-started_at) < 3600 THEN '15m-1h'
                    WHEN (ended_at-started_at) < 10800 THEN '1-3h'
                    ELSE '>3h' END b,
               COUNT(*) n, SUM(estimated_cost_usd) est
        FROM sessions GROUP BY b ORDER BY MIN(ended_at-started_at)
    """):
        print(f"  {r['b']:<8} sess={r['n']:>3}  est=${r['est'] or 0:>7.2f}")

def main():
    do_breakdown = None
    if "--breakdown" in sys.argv:
        do_breakdown = sys.argv[sys.argv.index("--breakdown") + 1]
    profiles = discover_profiles()
    if do_breakdown:
        db = profiles.get(do_breakdown)
        if not db or not os.path.exists(db):
            print(f"Нет state.db для профиля '{do_breakdown}'. Доступны: {', '.join(p for p,d in profiles.items() if d and os.path.exists(d))}")
            sys.exit(1)
        breakdown(db, do_breakdown)
        return
    print(f"{'Профиль':<16} {'Сессий':>7} {'Input':>11} {'Output':>11} {'Cache-read':>13} {'Расход':>9}  Период")
    gi = go = gc = ge = 0
    for name, db in profiles.items():
        s = profile_summary(name, db)
        if not s:
            print(f"{name:<16} {'—':>7}  (нет state.db — профиль не использовался)")
            continue
        gi += s["inp"]; go += s["out"]; gc += s["cr"]; ge += s["est"]
        print(f"{name:<16} {s['n']:>7} {s['inp']:>11,} {s['out']:>11,} {s['cr']:>13,} ${s['est']:>7.2f}  {s['first']} .. {s['last']}")
    print(f"{'ИТОГО':<16} {'':>7} {gi:>11,} {go:>11,} {gc:>13,} ${ge:>7.2f}")

    print("\n=== ПО МОДЕЛЯМ (все профили) ===")
    for name, db in profiles.items():
        if not db or not os.path.exists(db):
            continue
        for r in q(db, """
            SELECT model, COUNT(*) calls, SUM(input_tokens) inp, SUM(output_tokens) out,
                   SUM(cache_read_tokens) cr, SUM(reasoning_tokens) rs,
                   SUM(estimated_cost_usd) est
            FROM session_model_usage GROUP BY model ORDER BY est DESC
        """):
            print(f"{r['model']:<28} calls={r['calls']:>4}  inp={r['inp'] or 0:>9,}  out={r['out'] or 0:>9,}  cr={r['cr'] or 0:>12,}  rs={r['rs'] or 0:>8,}  ${r['est'] or 0:>7.2f}")

    print("\n=== ПО МЕСЯЦАМ (все профили) ===")
    for name, db in profiles.items():
        if not db or not os.path.exists(db):
            continue
        for r in q(db, """
            SELECT strftime('%Y-%m', started_at, 'unixepoch') m, COUNT(*) n,
                   SUM(input_tokens) inp, SUM(output_tokens) out, SUM(cache_read_tokens) cr,
                   SUM(reasoning_tokens) rs, SUM(estimated_cost_usd) est
            FROM sessions GROUP BY m ORDER BY m
        """):
            print(f"{name:<16} {r['m']}  sess={r['n']:>3}  inp={r['inp'] or 0:>9,}  out={r['out'] or 0:>9,}  cr={r['cr'] or 0:>12,}  rs={r['rs'] or 0:>8,}  ${r['est'] or 0:>7.2f}")

if __name__ == "__main__":
    main()
