#!/usr/bin/env python3
"""Aggregate Hermes token usage across all profiles from state.db SQLite stores.
Usage: python3 aggregate_profiles.py
Read-only (opens DBs with mode=ro). Prints per-profile totals, model breakdown,
monthly breakdown, and a JSON dump for scripting."""
import sqlite3, os, json
from datetime import datetime

HOME = os.path.expanduser("~")
profiles = {
    "default": f"{HOME}/.hermes/state.db",
    "developer": f"{HOME}/.hermes/profiles/developer/state.db",
    # add other profiles here, e.g.:
    # "japanese-tutor": f"{HOME}/.hermes/profiles/japanese-tutor/state.db",
}

def ts(epoch):
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d") if epoch else None

def q(db, sql, args=()):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()

summary = {}
for pname, db in profiles.items():
    if not db or not os.path.exists(db):
        summary[pname] = None
        continue
    r = q(db, """
        SELECT COUNT(*) as n_sessions,
               COALESCE(SUM(input_tokens),0) as inp,
               COALESCE(SUM(output_tokens),0) as out,
               COALESCE(SUM(cache_read_tokens),0) as cr,
               COALESCE(SUM(cache_write_tokens),0) as cw,
               COALESCE(SUM(reasoning_tokens),0) as rs,
               COALESCE(SUM(estimated_cost_usd),0) as est,
               COALESCE(SUM(actual_cost_usd),0) as act,
               COALESCE(SUM(api_call_count),0) as api,
               MIN(started_at) as first_s,
               MAX(started_at) as last_s,
               COALESCE(SUM(tool_call_count),0) as tools
        FROM sessions
    """)[0]
    models = q(db, """
        SELECT model,
               COUNT(*) as calls,
               SUM(input_tokens) as inp,
               SUM(output_tokens) as out,
               SUM(cache_read_tokens) as cr,
               SUM(cache_write_tokens) as cw,
               SUM(reasoning_tokens) as rs,
               SUM(estimated_cost_usd) as est,
               SUM(actual_cost_usd) as act
        FROM session_model_usage
        GROUP BY model ORDER BY act DESC
    """)
    months = q(db, """
        SELECT strftime('%Y-%m', started_at, 'unixepoch') as m,
               COUNT(*) as n,
               SUM(input_tokens) as inp, SUM(output_tokens) as out,
               SUM(cache_read_tokens) as cr, SUM(cache_write_tokens) as cw,
               SUM(reasoning_tokens) as rs,
               SUM(estimated_cost_usd) as est, SUM(actual_cost_usd) as act
        FROM sessions GROUP BY m ORDER BY m
    """)
    summary[pname] = {
        "n_sessions": r["n_sessions"], "inp": r["inp"], "out": r["out"],
        "cr": r["cr"], "cw": r["cw"], "rs": r["rs"], "est": r["est"], "act": r["act"],
        "api": r["api"], "tools": r["tools"],
        "first": ts(r["first_s"]), "last": ts(r["last_s"]),
        "models": [dict(m) for m in models],
        "months": [dict(m) for m in months],
    }

print(json.dumps(summary, indent=2, default=str))
