#!/usr/bin/env python3
"""Deep dive into one Hermes session: structure, tool usage, heaviest messages.
Usage: python3 session_deep_dive.py <session_id>
Read-only. Key trick: messages.token_count is NULL in most DBs, so sizes are
measured with LENGTH(content) — divide by ~4 for a token estimate."""
import sqlite3, os, sys
from datetime import datetime

DB = os.path.expanduser("~/.hermes/profiles/developer/state.db")
SID = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: session_deep_dive.py <session_id>")

def q(sql, args=()):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()

sess = q("SELECT * FROM sessions WHERE id=?", (SID,))[0]
print(f"=== SESSION: {sess['title']} ===")
print(f"id={SID} model={sess['model']} source={sess['source']}")
print(f"input={sess['input_tokens']:,} output={sess['output_tokens']:,} "
      f"cache_read={sess['cache_read_tokens']:,} est=${sess['estimated_cost_usd'] or 0:.3f}")
print(f"api_calls={sess['api_call_count']} tools={sess['tool_call_count']} messages={sess['message_count']}")

# Content size by role/tool (chars) — token_count is NULL, use LENGTH
print("\n--- AVG/MAX CONTENT SIZE BY ROLE+TOOL (chars) ---")
for r in q("""
    SELECT role, tool_name, COUNT(*) n,
           ROUND(AVG(LENGTH(COALESCE(content,''))),0) avg_len,
           MAX(LENGTH(COALESCE(content,''))) max_len,
           SUM(LENGTH(COALESCE(content,''))) sum_len
    FROM messages WHERE session_id=?
    GROUP BY role, COALESCE(tool_name,'') ORDER BY sum_len DESC
""", (SID,)):
    print(f"{r['role']:<10} {str(r['tool_name'] or '-'):<30} n={r['n']:>4} "
          f"avg={r['avg_len']:>9,.0f} max={r['max_len']:>9,} sum={r['sum_len']:>12,}")

# Top heaviest messages
print("\n--- TOP-20 HEAVIEST MESSAGES ---")
for i, r in enumerate(q("""
    SELECT role, tool_name, LENGTH(COALESCE(content,'')) len,
           substr(COALESCE(content,''),1,90) snip
    FROM messages WHERE session_id=? ORDER BY len DESC LIMIT 20
""", (SID,)), 1):
    print(f"{i:>2}. len={r['len']:>8,} {r['role']:<10} {str(r['tool_name'] or '-'):<28} | {(r['snip'] or '').replace(chr(10),' ')[:70]}")

# Repeated identical tool calls (context duplication signal)
print("\n--- REPEATED IDENTICAL TOOL CALLS (n>2) ---")
for r in q("""
    SELECT tool_name, COUNT(*) n FROM messages
    WHERE session_id=? AND role='tool' AND content IS NOT NULL
    GROUP BY tool_name, content HAVING n > 2 ORDER BY n DESC LIMIT 10
""", (SID,)):
    print(f"n={r['n']:>3} {r['tool_name']}")

# Hourly activity timeline
print("\n--- ACTIVITY BY HOUR ---")
for r in q("""
    SELECT CAST((timestamp - ?) / 3600 AS INT) h, COUNT(*) n
    FROM messages WHERE session_id=? GROUP BY h ORDER BY h
""", (sess['started_at'], SID)):
    print(f"h={r['h']:>3}  msgs={r['n']:>3}  {'#' * min(int(r['n']/10)+1, 40)}")

# Compression status
print("\n--- COMPRESSION ---")
print("compacted messages:", q("SELECT COUNT(*) n FROM messages WHERE session_id=? AND compacted=1", (SID,))[0]["n"])
print("compression locks:", len(q("SELECT * FROM compression_locks WHERE session_id=?", (SID,))))
