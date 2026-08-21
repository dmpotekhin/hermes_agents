#!/usr/bin/env python3
"""Ad-hoc verification for coding-agent-config output files.
Usage: python3 verify-configs.py [dir]  (default: current dir)
Checks opencode.json (strict JSON), kilo.jsonc (JSONC: comments stripped),
graphify.sh (bash -n + executable bit). Exit 0 = all OK.
"""
import json
import os
import re
import subprocess
import sys

base = sys.argv[1] if len(sys.argv) > 1 else "."
fails = []

# 1. opencode.json — строгий JSON + ключевые поля
p = os.path.join(base, "opencode.json")
if os.path.exists(p):
    try:
        cfg = json.load(open(p))
        assert "provider" in cfg, "нет секции provider"
        assert "model" in cfg, "нет model"
        print("opencode.json: OK")
    except Exception as e:
        fails.append(f"opencode.json: {e}")
else:
    print("opencode.json: пропущен (нет файла)")

# 2. kilo.jsonc — JSONC: выкинуть //-комментарии, проверить как JSON
p = os.path.join(base, "kilo.jsonc")
if os.path.exists(p):
    try:
        raw = open(p).read()
        stripped = re.sub(r"//[^\n]*", "", raw)
        k = json.loads(stripped)
        assert "instructions" in k, "нет instructions"
        print("kilo.jsonc: OK")
    except Exception as e:
        fails.append(f"kilo.jsonc: {e}")
else:
    print("kilo.jsonc: пропущен (нет файла)")

# 3. graphify.sh — синтаксис bash + executable
p = os.path.join(base, "graphify.sh")
if os.path.exists(p):
    try:
        r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert os.stat(p).st_mode & 0o111, "не executable"
        print("graphify.sh: OK")
    except Exception as e:
        fails.append(f"graphify.sh: {e}")
else:
    print("graphify.sh: пропущен (нет файла)")

if fails:
    print("FAILED:")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("ALL OK")
