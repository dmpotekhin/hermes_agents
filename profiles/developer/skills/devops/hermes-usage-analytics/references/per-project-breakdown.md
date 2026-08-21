# Per-project / per-day token cost breakdown

The aggregator script (analyze_usage.py) shows totals by day/model/source, but when
the user asks «сколько потрачено на проект X сегодня» (sessions have descriptive
titles like "Improving Travel Visualiser Routing and Maps #4"), run these SQL
queries directly against the profile's state.db (READ-ONLY only!):

```
DB="file:/Users/<user>/.hermes/profiles/<profile>/state.db?mode=ro"

# 1) Sessions for a specific day, ordered by cost
sqlite3 -header -column "$DB" \
"SELECT datetime(started_at,'unixepoch','localtime') AS start,
        source, model, message_count AS msg, tool_call_count AS tools,
        printf('%.2f',COALESCE(estimated_cost_usd,0)) AS est\$,
        substr(COALESCE(title,''),1,60) AS title
 FROM sessions
 WHERE date(started_at,'unixepoch','localtime')='2026-08-19'
 ORDER BY estimated_cost_usd DESC;"

# 2) Group by task/project via title patterns (daily sums)
sqlite3 -header -column "$DB" \
"SELECT CASE
          WHEN title LIKE '%Travel Visualiser%' THEN 'Travel Visualiser'
          WHEN title LIKE '%парсинг%' THEN 'scraping eval'
          ELSE 'прочее' END AS group_name,
        COUNT(*) AS sess, SUM(input_tokens) AS inp, SUM(output_tokens) AS out,
        printf('%.2f',SUM(COALESCE(estimated_cost_usd,0))) AS est\$
 FROM sessions
 WHERE date(started_at,'unixepoch','localtime')='2026-08-19'
 GROUP BY group_name ORDER BY est\$ DESC;"
```

## Notes

- Always report estimated_cost_usd as «оценка» — providers (DeepSeek etc.) rarely
  return actual billing data.
- Cache-read tokens dominate (~90% of traffic) but are cheap; mention that real
  spend is input+output+reasoning.
- Session titles come from the first user message — repeated work on the same
  feature shows up as "Title #2", "#3" … use LIKE patterns with the base title.
- Commands piping curl|python3 hit the approval gate; for JSON API queries write
  to /tmp first, then parse. For sqlite3 the plain CLI needs no gate.
