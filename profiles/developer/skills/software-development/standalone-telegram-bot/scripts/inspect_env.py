#!/usr/bin/env python3
"""Показать, какие переменные заполнены в .env, НЕ раскрывая значений.

Использование:
    python3 inspect_env.py <путь-к-.env> [ОБЯЗАТЕЛЬНАЯ_ПЕРЕМЕННАЯ ...]

Для каждой переменной печатает одно из: ПУСТО / похоже на плейсхолдер /
заполнено (N символов). Значения, их префиксы и хвосты не выводятся никогда.
Код возврата: 0 — все обязательные заполнены, 1 — есть пустые/файла нет.
"""

from __future__ import annotations

import pathlib
import sys

PLACEHOLDER_HINTS = ("your_", "xxx", "changeme", "example", "<token", "paste")


def parse_env(path: pathlib.Path) -> dict[str, str]:
    """Разобрать .env в словарь (без раскрытия значений наружу)."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw = line.partition("=")
        values[key.strip()] = raw.strip().strip('"').strip("'")
    return values


def describe(value: str) -> str:
    """Описать состояние переменной, не раскрывая значение."""
    if not value:
        return "ПУСТО"
    lowered = value.lower()
    if any(hint in lowered for hint in PLACEHOLDER_HINTS):
        return "похоже на плейсхолдер"
    return f"заполнено ({len(value)} символов)"


def main(argv: list[str]) -> int:
    """Точка входа CLI."""
    if len(argv) < 2:
        print(__doc__)
        return 2

    path = pathlib.Path(argv[1]).expanduser()
    required = argv[2:]

    if not path.exists():
        print(f"НЕТ ФАЙЛА: {path}")
        print(f"Создай его из шаблона: cp {path.parent}/.env.example {path}")
        return 1

    values = parse_env(path)
    print(f"{path} ({path.stat().st_size} байт)")
    for key, value in values.items():
        print(f"  {key}: {describe(value)}")

    missing = [key for key in required if not values.get(key)]
    print("Не хватает обязательных:", ", ".join(missing) if missing else "нет")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
