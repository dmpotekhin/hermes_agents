#!/usr/bin/env python3
"""Fetch server-side-rendered page(s) with a browser UA, extract readable text.

Use when an extraction front-end (web_extract / r.jina.ai path) refuses a URL
with a "private or internal network address" anti-bot block, but the site
actually serves plain SSR HTML. Handles Nextra/Next.js (`<main>`) and generic
pages (`<body>` minus scripts/styles).

Usage:
    fetch_ssr_page.py <url> [<url> ...]
"""
import html
import re
import sys
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
BLOCK_MARKERS = (
    "This page could not be found",
    "Just a moment",
    "Attention Required",
    "Verify you are human",
)


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def extract_text(doc: str) -> str:
    m = re.search(r"<main[^>]*>(.*?)</main>", doc, re.S)
    if not m:
        m = re.search(r"<body[^>]*>(.*?)</body>", doc, re.S)
    blob = m.group(1) if m else doc
    blob = re.sub(r"<script.*?</script>", "", blob, flags=re.S)
    blob = re.sub(r"<style.*?</style>", "", blob, flags=re.S)
    blob = re.sub(r"<[^>]+>", " ", blob)
    blob = html.unescape(blob)
    blob = re.sub(r"[ \t]+", " ", blob)
    blob = re.sub(r"\n\s*\n+", "\n", blob)
    return blob.strip()


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: fetch_ssr_page.py <url> [<url> ...]", file=sys.stderr)
        return 2
    for url in argv:
        print("=" * 70)
        print("PAGE:", url)
        try:
            doc = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print(f"ERR {exc!r}")
            continue
        text = extract_text(doc)
        marker = next((m for m in BLOCK_MARKERS if m in text), None)
        if marker:
            print(
                f"WARN: looks like a block/404 page (marker: {marker!r}); "
                "try another URL or an archive route",
                file=sys.stderr,
            )
        print(text if text else f"(no extractable content) — {len(doc)} bytes raw")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
