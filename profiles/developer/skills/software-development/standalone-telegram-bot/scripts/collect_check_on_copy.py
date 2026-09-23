"""Run one collection against a COPY of the live DB, with the LLM layer off.

Why: prove every registry source still collects (no stale feed URL, no 301
chain, no timeout) without touching the live DB and without spending tokens.

Usage:
    cd ~/projects/tg-transcriber && ./.venv/bin/python \
        <this-file>

Override the repo with TG_TRANSCRIBER_REPO. Field names below follow the news
service of that repo; adjust if its property names move. Exit code: 0 = all
sources collected, 1 = at least one failed (its error is printed).
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(os.environ.get("TG_TRANSCRIBER_REPO", "~/projects/tg-transcriber")).expanduser()
sys.path.insert(0, str(REPO))
# Only the collection is under test: keep the per-item analysis layer off.
os.environ.setdefault("NEWS_AGENTIC_ENABLED", "false")

from services.news.config import read_news_settings  # noqa: E402
from services.news.processors.classifier import NewsClassifier  # noqa: E402
from services.news.service import NewsService  # noqa: E402
from services.news.storage.repository import NewsRepository  # noqa: E402


def copy_database(source: Path) -> Path:
    """Copy the DB through the backup API.

    Args:
        source: path of the live database.

    Returns:
        Path of the copy in a temp directory. A plain `cp` would drop the
        unwritten WAL and report fewer rows than the service sees.
    """
    target = Path(tempfile.mkdtemp()) / source.name
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(target)
    with dst:
        src.backup(dst)
    src.close()
    dst.close()
    return target


def main() -> int:
    """Collect once on the copy and report source health."""
    live = REPO / "news.db"
    reader = sqlite3.connect(f"file:{live}?mode=ro", uri=True)
    items_before = reader.execute("select count(*) from items").fetchone()[0]
    reader.close()

    repository = NewsRepository(copy_database(live))
    settings = read_news_settings()
    service = NewsService(settings, repository=repository)
    # Deterministic classifier: importance/relevance without an LLM call.
    service.classifier = NewsClassifier(
        settings, llm=None, relevance=service.relevance, repository=repository
    )

    # The report carries per-stage timestamps, not a duration — measure locally.
    started = time.monotonic()
    outcome = asyncio.run(service.collect())
    elapsed = time.monotonic() - started
    report = outcome.report

    print("ok:", outcome.ok, "| error:", outcome.error or "нет")
    print(f"sources ok: {report.sources_ok} | failed: {report.sources_failed}")
    print(
        f"collected: {report.collected} | duplicates: {report.duplicates}"
        f" | stored: {report.stored} | important: {report.important}"
    )
    print(f"seconds: {elapsed:.1f} (baseline for ~30 feeds: single digits)")
    print("failed sources:", report.source_errors or "none")
    print("items: copy", repository.total_items(), "| live", items_before)
    repository.close()
    return 0 if report.sources_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
