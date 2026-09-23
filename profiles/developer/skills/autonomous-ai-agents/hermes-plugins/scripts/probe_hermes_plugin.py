#!/usr/bin/env python3
"""Probe an installed Hermes plugin (load, register tools, call handlers) and the
plugin registry state (`hermes plugins list`, parsed by table delimiter).

Usage:
    probe_hermes_plugin.py <plugin-dir>            # both parts
    probe_hermes_plugin.py <plugin-dir> --no-list  # load/register probe only
    probe_hermes_plugin.py --no-load               # registry table only

Run part 1 with the HERMES venv interpreter so plugin imports resolve:
    /Users/<you>/.hermes/hermes-agent/venv/bin/python3 \
        probe_hermes_plugin.py "$HERMES_HOME/plugins/agency-agents-router"

Why: plugin tools only register at Hermes STARTUP, so a mid-session update cannot be
exercised through the agent's own tool list. This loads the artifacts on disk the way the
host does (register(ctx), handlers called as handler(args)) and proves they work.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path

ENTRYPOINTS = ("register", "setup", "register_plugin", "plugin_entry")


class RecordingCtx:
    """Minimal stand-in for Hermes' PluginContext."""

    def __init__(self) -> None:
        self.tools: dict[str, dict] = {}

    def register_tool(self, **kwargs):
        self.tools[kwargs.get("name", "<?>")] = kwargs

    def __getattr__(self, item):  # tolerate anything else the plugin pokes at
        def _stub(*_a, **_k):
            return None

        return _stub


SAMPLE_ARGS = {
    "query": "software architect",
    "agent": "software-architect",
    "task": "design a service",
    "name": "software-architect",
}


def load_plugin(plugin_dir: Path) -> None:
    init = plugin_dir / "__init__.py"
    if not init.is_file():
        print(f"!! no __init__.py in {plugin_dir}")
        return

    spec = importlib.util.spec_from_file_location("plugin_probe_target", init)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    entry = next((n for n in ENTRYPOINTS if hasattr(mod, n)), None)
    if entry is None:
        print("!! no register/setup entrypoint found")
        return
    fn = getattr(mod, entry)
    print(f"entrypoint: {entry}{inspect.signature(fn)}")

    ctx = RecordingCtx()
    fn(ctx)  # NOTE: one positional arg — register(ctx), never register(None, ctx)
    print(f"tools registered: {len(ctx.tools)} -> {sorted(ctx.tools)}")

    for name, spec_ in ctx.tools.items():
        handler = spec_.get("handler")
        if handler is None:
            continue
        params = inspect.signature(handler).parameters
        args = {k: v for k, v in SAMPLE_ARGS.items()}
        try:
            out = handler(args) if len(params) < 2 else handler(args, ctx)
        except Exception as exc:  # noqa: BLE001
            print(f"  {name} -> ERROR {type(exc).__name__}: {exc}")
            continue
        try:
            payload = json.loads(out) if isinstance(out, str) else out
        except Exception:  # noqa: BLE001
            print(f"  {name} -> non-JSON output: {str(out)[:80]}")
            continue
        if isinstance(payload, dict):
            for key in ("results", "matches", "agents"):
                if isinstance(payload.get(key), list):
                    hits = payload[key]
                    labels = [h.get("slug") or h.get("name") for h in hits[:3]
                              if isinstance(h, dict)]
                    print(f"  {name} -> {len(hits)} hits: {labels}")
                    break
            else:
                print(f"  {name} -> keys: {sorted(payload)[:8]}")
        else:
            print(f"  {name} -> {str(payload)[:80]}")

    # roster-style data file, if present
    for cand in (plugin_dir / "data" / "agents.json", plugin_dir / "data" / "items.json"):
        if cand.is_file():
            data = json.loads(cand.read_text())
            n = len(data) if isinstance(data, list) else len(data.get("agents", data))
            print(f"{cand.name}: {n} entries")


def list_registry(needle: str | None = None) -> None:
    """Parse `hermes plugins list` by the box-drawing delimiter (the table WRAPS, so
    grepping the raw text can match a description cell of an unrelated plugin)."""
    out = subprocess.run(["hermes", "plugins", "list"], capture_output=True, text=True)
    if out.returncode != 0:
        print(f"!! `hermes plugins list` failed: {out.stderr.strip()[:200]}")
        return
    rows = []
    for line in out.stdout.splitlines():
        if "│" not in line:
            continue
        cells = [c.strip() for c in line.split("│")[1:-1]]
        if len(cells) < 5 or cells[0] in ("Name", "") or set(cells[0]) <= {"─"}:
            continue
        rows.append(cells[:5])
    print(f"registry rows: {len(rows)}")
    shown = [r for r in rows if needle is None or needle.lower() in r[0].lower()]
    if not shown:
        print(f"  !! no plugin row matching {needle!r} — check the plugin is in THIS profile's "
              "plugins dir (discovery is profile-scoped)")
    for name, status, version, _desc, source in shown:
        print(f"  {name:32s} {status:14s} {version:8s} {source}")


def main(argv: list[str]) -> int:
    plugin_dir = None
    for a in argv:
        if not a.startswith("--") and Path(a).is_dir():
            plugin_dir = Path(a).expanduser()
    if plugin_dir is not None and "--no-load" not in argv:
        print(f"=== load/register probe: {plugin_dir} ===")
        load_plugin(plugin_dir)
        print()
    if "--no-list" not in argv:
        print("=== registry (`hermes plugins list`) ===")
        needle = plugin_dir.name if plugin_dir is not None else None
        list_registry(needle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
