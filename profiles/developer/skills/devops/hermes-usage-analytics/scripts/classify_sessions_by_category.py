#!/usr/bin/env python3
"""Classify Hermes sessions into categories and sum tokens/cost per category.

Answers: «сколько потрачено на архитектуру / спеки / разработку / тестирование?»

Usage:
    python3 classify_sessions_by_category.py [profile]   # default: developer

Read-only connection to <profile>/state.db. Categories are inferred from
session title keywords; untitled subagent sessions are attributed to their
parent session via parent_session_id (otherwise ~half the sessions land in
«Прочее» and the breakdown is meaningless).

Output: per-category table (Input / Output / Cache-read / TOTAL) plus
deepseek-only cost vs all-models cost, and a list of cost anomalies.

Pitfalls handled:
  - subagent rows have empty titles -> effective title = parent's title
  - estimated_cost_usd is junk for one-off HF-router calls (GLM, Qwen,
    HF deepseek calls): a single call can show $74K. Trust only
    model LIKE 'deepseek-%' rows for cost; tokens are always reliable.
  - sessions.reasoning_tokens exists; alias it in SQL and use the ALIAS in
    code (IndexError if you reference the raw column name on a Row).
"""

import sqlite3
import re
import sys
import os
from datetime import datetime

PROFILE = sys.argv[1] if len(sys.argv) > 1 else "developer"
HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
DB = f"file:{os.path.join(HERMES_HOME, 'profiles', PROFILE, 'state.db')}?mode=ro"

CATEGORY_ORDER = ["Архитектура", "Спеки / планирование", "Разработка", "Тестирование", "Прочее"]

RULES = [
    ("Архитектура", r"архитектур|architect|дизайн|проектирован|design|фреймворк|framework|gsd|концепц"),
    ("Спеки / планирование", r"спек|spec\b|спецификац|план|планир|planning|документац|documentation|readme"),
    ("Тестирование", r"тест|test|qa|проверк|verification|verify|тренажёр|тренажер|регресс|kafka"),
    ("Разработка", r"разработ|реализац|создан|запуск|портирован|добавлен|исправлен|обновлен|improving|"
                    r"продолжен|конструктор|интеграц|настро|установ|генерац|парсинг|parse|пул|push|пуш|"
                    r"автоматиз|оптимиз|аналог|книг|book|заметок|notes|ридер|reader|веб-прилож|визуализ|"
                    r"scraping|skill|скилл|плагин|plugin|агент|agent|wiki|rag|репозитори|путешеств|travel|"
                    r"oracle|content|контент|видео|присутствие|готовность|harness|sandbox|strix|docker|"
                    r"girmish|pireel|abacus|invisible|hugging face|модел|provider|провайдер|deploy|деплой|"
                    r"список|сортировк|заметк|тревел|вайбкодинг|отчёт|аналитика|статистик|гермеса|hermes|"
                    r"вопрос|integration|анализ"),
]


def classify(title: str) -> str:
    t = title.lower()
    for cat, pattern in RULES:
        if re.search(pattern, t):
            return cat
    return "Прочее"


def main():
    conn = sqlite3.connect(DB, uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT id, parent_session_id, started_at, source, model,
                  input_tokens, output_tokens, cache_read_tokens,
                  COALESCE(reasoning_tokens,0) AS reasoning,
                  COALESCE(estimated_cost_usd,0) AS cost,
                  COALESCE(title,'') AS title
           FROM sessions ORDER BY started_at"""
    ).fetchall()
    by_id = {r["id"]: r for r in rows}

    def eff_title(r):
        if r["title"]:
            return r["title"]
        p = by_id.get(r["parent_session_id"])
        return p["title"] if p and p["title"] else ""

    cats = {}
    for r in rows:
        t = eff_title(r) or "(без названия)"
        c = classify(t)
        e = cats.setdefault(c, dict(n=0, inp=0, out=0, cr=0, rs=0, deep=0.0, allcost=0.0))
        e["n"] += 1
        e["inp"] += r["input_tokens"] or 0
        e["out"] += r["output_tokens"] or 0
        e["cr"] += r["cache_read_tokens"] or 0
        e["rs"] += r["reasoning"] or 0
        e["allcost"] += r["cost"] or 0
        if r["model"].startswith("deepseek"):
            e["deep"] += r["cost"] or 0

    print(f"{'Категория':<26}{'сесс':>5}{'Input':>12}{'Output':>11}{'Cache-read':>14}{'ВСЕГО':>15}")
    tot = dict(n=0, inp=0, out=0, cr=0, rs=0, deep=0.0, allcost=0.0)
    for c in CATEGORY_ORDER:
        e = cats.get(c, dict(n=0, inp=0, out=0, cr=0, rs=0, deep=0.0, allcost=0.0))
        all_t = e["inp"] + e["out"] + e["cr"] + e["rs"]
        print(f"{c:<26}{e['n']:>5}{e['inp']:>12,}{e['out']:>11,}{e['cr']:>14,}{all_t:>15,}")
        for k in tot:
            tot[k] += e[k]
    all_t = tot["inp"] + tot["out"] + tot["cr"] + tot["rs"]
    print(f"{'ИТОГО':<26}{tot['n']:>5}{tot['inp']:>12,}{tot['out']:>11,}{tot['cr']:>14,}{all_t:>15,}")

    print("\nОценка стоимости: deepseek-модели (достоверно) vs все модели (вкл. мусор HF-роутера)")
    for c in CATEGORY_ORDER:
        e = cats.get(c, dict(n=0, deep=0.0, allcost=0.0))
        print(f"  {c:<26} deepseek=${e['deep']:>8.2f}   все=${e['allcost']:>10.2f}")
    print(f"  {'ИТОГО':<26} deepseek=${tot['deep']:>8.2f}   все=${tot['allcost']:>10.2f}")

    print("\nАномальные оценки стоимости (>$1 — обычно мусор прайсов HF-роутера):")
    for r in rows:
        if r["cost"] > 1:
            print(f"  {datetime.fromtimestamp(r['started_at']).strftime('%m-%d')} "
                  f"[{r['source']}] {eff_title(r)[:60] or '(no title)'} "
                  f"cost=${r['cost']:.2f} model={r['model']}")


if __name__ == "__main__":
    main()
