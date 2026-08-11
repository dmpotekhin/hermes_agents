# Task 9 — Kids Learn global CSS (frontend design system)

Brief gave the full `frontend/src/styles/index.css` verbatim. The deliverable was a clean,
complete CSS file plus a build-verify gate. Wrote it as-is (an empty file was scaffolded in
Task 8; `App.jsx` already imports `./styles/index.css`).

## The one deliberate, spec-required deviation from the brief

The brief placed the Google-Fonts `@import` **mid-file** (after the `:root` and `body`
rules). CSS spec requires `@import` to precede **all** other rules (except `@charset` /
`@layer`); a mid-file import is dropped or warned by conforming parsers/bundlers. Moved it
to the top as the first statement, keeping the comment. All 61 rule bodies stayed byte-identical.

**Rule of thumb for CSS briefs:** if a brief's embedded CSS has `@import` after the first
`{ }` rule, move it to the top of the file — it is an authoring error, and fixing it aligns
with (not contradicts) the brief's intent. Flag it in the report as a deliberate deviation.

## Verifying a transcribed CSS artifact against the brief

The build gate here is not a real signal for CSS correctness (`vite build` only fails on the
still-missing `./pages/*` imports owned by later tasks — ad-hoc status), so verify the CSS
*content* directly against the brief's embedded code fence:

```python
import re
brief = open(".../task-9-brief.md").read()
css   = open(".../frontend/src/styles/index.css").read()
mb = re.search(r"```css\n(.*?)```", brief, re.DOTALL).group(1)

def strip_(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.DOTALL)      # strip comments
    t = re.sub(r"@import[^;]+;", "", t, flags=re.DOTALL)  # strip @import (position moves)
    return t
def split_rules(t):              # brace-aware: splits on '}', survives inside of } blocks
    buf, rules = "", []
    for ch in t:
        buf += ch
        if ch == "}": rules.append(buf); buf = ""
    if buf.strip(): rules.append(buf)
    return [r for r in rules if r.strip()]
norm = lambda s: re.sub(r"\s+", " ", s).strip()
def body(r): return r[r.index("{")+1:] if "{" in r else r

wb  = sorted(body(norm(r)) for r in split_rules(strip_(css)))
bb  = sorted(body(norm(r)) for r in split_rules(strip_(mb)))
assert wb == bb, "CSS bodies differ from brief"   # + check len == 61, vars, keyframes
```

Also assert: balanced braces `css.count("{")==css.count("}")`, all `:root` vars present,
`@keyframes <name>` present, and `css.index("@import") < css.index(":root")` (import is first).

### Why naive checks give false failures (pitfalls the probe must avoid)
These are bugs in the **verification probe**, not the CSS — a probe that reports "missing
rule" here is wrong about the file, and trusting it would make you "fix" correct code:
- **Raw-file substring match fails on whitespace.** `b not in css` against the *raw* file
  is false whenever surrounding newlines/indentation differ, even though the rule is
  byte-equivalent once whitespace-normalized. Compare **normalized forms** on both sides.
- **`@keyframes { from { … } to { … } }` produces nested `{ }`**, so splitting rules on `}`
  yields fragments like `@keyframes x { from { opacity:0 }` with no preceding `{` reachable
  by `.index("{")` at the rule start. Extract body as `r[r.index("{")+1:] if "{" in r else r`
  and treat brace-less fragments as skip/noise.
- **`@import` repositioning merges into its old neighbor.** In the brief, `@import` sits
  between `:root{…}` and `.container{…}`, so a naive `}`-split folds it into one of them; the
  *missing*-rule report then blames `:root`/`.container`, which are actually intact. Strip
  `@import` from BOTH texts before splitting to sidestep this entirely.

## Build-verify (repeats Task 8 nuance but explicit for CSS tasks)
- Default system `node` is v14 here; `vite build` (rolldown) crashes under it with
  `SyntaxError: Unexpected token '??='`. Use nvm Node ≥20.19:
  `source ~/.nvm/nvm.sh && nvm use 20` then `npm run build`.
- Full build stays red on `./pages/HomePage` / `./pages/LessonPage` unresolved imports —
  intended pending-import for later tasks, not a defect. State the report's verification is
  **ad-hoc** (no canonical suite), and that a CSS task's true gate is the content check above.
- `git add frontend/src/styles/` then commit with the brief's message.
