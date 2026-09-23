# Collector & feed health (RSS/API aggregator inside a bot)

For a bot that aggregates feeds on a schedule (news radar, digest bot, price
watcher). Symptoms covered: "collection takes minutes", "the same few sources
error every run", "did my change break collection?".

## Feed URLs must point at the FINAL address

A `feed_url` that redirects costs the source its whole timeout budget: the
request follows 301 → 301 → 200 and lands on the per-source timeout, so the
source is reported failed while a plain curl gets 200 in under a second. Two or
three such sources are enough to stretch a cycle from seconds to over a minute,
which then looks like collector load or concurrency problems.

Known shape: Hubbub-style paths that moved from a singular hub segment to a
plural one plus a trailing content path (`/rss/hub/<x>/all/` →
`/rss/hubs/<x>/articles/all`), i.e. a two-hop redirect chain.

Probe before trusting a URL (the UA matters — several feeds 403 a bare curl):

```
curl -s -o /tmp/feed.xml -w '%{http_code} %{redirect_url}\n' -A 'Mozilla/5.0' "$URL"
grep -c '<item>' /tmp/feed.xml
```

Expect `200` with an EMPTY `redirect_url` and a non-zero item count. The
registry is data, so the fix is a one-line `feed_url` change plus a regression
test over the registry asserting no source uses the known-redirect path — those
tests must not touch the network (assert over the registry objects only).

## Dry run on a DB copy, expensive layer OFF

1. Copy the live DB with the backup API, never `cp`: the service runs under
   launchd and holds a WAL, so a plain copy yields fewer rows and a false
   "migration lost data" verdict.
   `sqlite3.connect(f"file:{live}?mode=ro", uri=True)` → `src.backup(dst)`.
2. Force the expensive layer off (the aggregator's flag) and swap the
   LLM-backed classifier/scorer for a deterministic one (`llm=None` on the
   constructor) so the dry run spends no tokens.
3. Run exactly one cycle, print `sources_ok` / `sources_failed` / `source_errors`
   (a dict source → error) and the item counts in copy vs live — the latter
   proves the live DB was not touched.
4. Measure elapsed yourself: these report objects usually carry per-stage
   timestamps, not a `duration` attribute — reading `report.duration_seconds`
   raises `AttributeError` after the collection has already run.

Baseline for ~30 feeds: `sources_failed = 0`, single-digit seconds. Treat any
failed source as a regression and exit non-zero so the check can gate a change.
Ready to run: `scripts/collect_check_on_copy.py` (defaults to
`~/projects/tg-transcriber`; override with `TG_TRANSCRIBER_REPO`). Field names
there follow the news service — adjust if the property names move.

## Do not diagnose a "stuck" collector before checking stage timings

The complaint ("collecting for N minutes, no answer") is usually a stale UI
status message rather than the collector: find the cycle's done-line in the log
with a time filter first. If the stage finished, the defect is in delivery or in
not replacing the status message, and the collector needs no change.
