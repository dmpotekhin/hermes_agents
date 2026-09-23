# Version check & safe update — worked transcript (2026-09-18)

Session asked "the latest version of hermes agent" on a macOS CLI profile. The install was
healthy (no recovery noise) but **diverged from upstream**, which is what actually blocks an
update. Everything below is real command output, except the update sequence in step 5.

## 1. Installed state

```
$ hermes --version
Hermes Agent v0.21.0 (2026.8.31) · upstream 63279301 · local 00b32292 (+1 carried commit)
Install directory: /Users/dmitrypotekhin/.hermes/hermes-agent
Install method: git
Python: 3.11.7
OpenAI SDK: 2.24.0
```

Read it as: install method `git` (so `~/.hermes/hermes-agent` IS a checkout), version+date,
and `local <sha> (+1 carried commit)` — the flag that a side branch is checked out.

## 2. Latest available

```
$ curl -s https://api.github.com/repos/NousResearch/hermes-agent/releases/latest
v2026.9.14 | Hermes Agent v0.21.3 (v2026.9.14) | 2026-09-14T16:04:14Z

$ curl -s "https://api.github.com/repos/NousResearch/hermes-agent/tags?per_page=8"
v2026.9.14  v2026.9.11  v2026.9.7  v2026.8.31  v2026.8.27  v2026.8.19  v2026.8.18  v2026.8.16.2
```

So: stable release **v0.21.3 / v2026.9.14**; `origin/main` was `c661785f87` (2026-09-18),
i.e. bleeding edge runs a few days ahead of the release tag. Offer both, stable first.

## 3. Velocity — why the commit count is not alarming

```
$ git fetch --tags origin     # pulls v2026.9.7 / v2026.9.11 / v2026.9.14
$ git rev-list --count HEAD..v2026.9.14        -> 7086
$ git rev-list --count --since=2026-09-05 origin/main -> 4590   (~350 commits/day)
```

Report the number as context, never as an emergency. Tags are weekly-ish; a 13-day-old
checkout is genuinely thousands of commits behind.

## 4. Why updating here is not a one-liner

```
$ git branch --show-current          -> dmitry/readme-restore      (NOT main)
$ git log --oneline origin/main..HEAD -> 00b3229277 docs: restore README beautify + agent architecture README
$ git merge-base --is-ancestor HEAD v2026.9.14   -> NO - diverged
$ git status --short                 -> ?? .update-incomplete.bak
$ ls -la .update-incomplete.bak      -> 15 bytes, JSON, 3 Sep 23:41
$ read_file .update-incomplete       -> File not found
```

Conclusions worth carrying forward:

- A **side branch + 1 carried commit** means `hermes update` may conflict or drop the local
docs commit. Resolve the carried commit first (patch-id compare against the tag), return to
`main` or check out the release tag, then update.
- **`HEAD` not being an ancestor of the tag is the blocker.** Say that outright instead of
quoting the version gap.
- **`.update-incomplete.bak` alone is residue.** The live marker (`.update-incomplete`) was
already gone, so there was no interrupted-update retry loop — the `.bak` is just a leftover
from an earlier recovery. Do not delete it as a "fix"; mention it and move on.

## 5. Planned (NOT yet executed) update order

Given to the user as a proposal, pending approval:

```bash
cd ~/.hermes/hermes-agent
git checkout main && git merge --ff-only origin/main    # or: git checkout v2026.9.14
# verify whether the carried README commit already landed upstream first:
#   git show HEAD | git patch-id --stable   vs the same for the target tag's history
hermes update
hermes --version && hermes doctor
rm -f .update-incomplete.bak
```

Unverified as of this writing — the approval gate blocked `hermes update --help` and the user
had not answered the clarify prompt. Do not cite it as a proven procedure.

## 6. Approval-gate behaviour observed

- `cat .update-incomplete; hermes update --help` → `BLOCKED: … the user has NOT consented`.
- A long `for c in $(git log …) … done` pipeline (patch-id sweep over thousands of commits)
  was blocked the same way.
- A `curl … | python3 -c …` parse was flagged HIGH by the security scanner (`Pipe to
  interpreter`) and required explicit approval.

Lesson: one simple command per call, fetch-then-parse instead of piping into an interpreter,
and treat any `BLOCKED` / timed-out-clarify as "stop and report", never as a cue to retry a
variant.
