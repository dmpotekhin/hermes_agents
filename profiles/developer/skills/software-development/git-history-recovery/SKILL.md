---
name: git-history-recovery
description: "Use when git work seems lost or a remote looks like a fork."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [git, reflog, fsck, cherry-pick, fork, recover, remote]
---

# Git History Recovery & Fork Verification

Two related, recurring git-surgery problems: work that "disappeared" from a branch, and pushing to a remote that only *looks* like a fork. Both are non-destructive to diagnose and easy to get wrong — read before acting.

## When to use

- `git status` is clean / up-to-date with upstream, but the user says "I made edits in my IDE / my changes are gone."
- A merge/rebase/update left the branch on upstream `main` and the user's commits aren't visible.
- The user names a repo as "my fork" and asks you to push, but the remote's true nature is unconfirmed.

---

## Part 1 — Recover "lost" commits (dangling / unreachable)

After a botched update (rebase abort → `reset` to a tag → `merge origin/main: Fast-forward`), the user's own commits fall off the branch **but the git objects are still alive**. They are *unreachable* — not in any ref/branch, which is exactly why `git status` looks pristine.

### Diagnose

```bash
# 1. Is the branch really clean & where does it point?
git status -sb
#   look for: "## main...origin/main" with 0 ahead/behind, OR a reflog full of abort/reset/merge

# 2. Reflog — shows the checkpoint trail, incl. commits that were later dropped
git reflog -15

# 3. List unreachable (dangling) commits — the user's lost work lives here
git fsck --no-reflogs --unreachable | grep commit

# 4. Identify each dangling commit
git show --stat --oneline <sha>   # author + changed files reveal WHICH is the user's
```

The user's commits usually have their name/email as author (`git show <sha> | head` on the Author line) and touch files they'd work on (README, docs, their module). A hash from a reflog entry like `commit: docs: ...` is the giveaway.

### Recover

Create a working branch off current main, then cherry-pick each lost commit with `--no-commit` (so you can inspect before committing):

```bash
git checkout -b <name>/recover main
git cherry-pick --no-commit <sha1>      # repeat per commit, oldest first
git cherry-pick --no-commit <sha2>
```

If a cherry-pick conflicts, resolve (see resolution tip below), then commit the assembled work:

```bash
git commit -m "docs: restore ... "
```

### Cherry-pick auto-merge is NOT enough for intentionally-redesigned files

`git cherry-pick -X ours` (or `-X theirs`) only auto-resolves the *contested* hunks and silently keeps the winner's text for them. For a file the user deliberately redesigned (README, docs, SVG assets), the auto-merge can drop their redesign. **`-X ours` means "keep OUR branch's version only on conflict" — it discards the source commit's intent for that hunk.**

Verify and restore verbatim:

```bash
# 1. Does the staged file match the SOURCE commit's exact blob?
git show <source-commit>:README.md > /tmp/ref.md
diff <(git show :README.md) /tmp/ref.md && echo "matches" || echo "DIFFERS — restore"

# 2. If it differs, take the source commit's exact version + re-add
git show <source-commit>:README.md > README.md
git add README.md
```

### Cleanup when it goes sideways

If you abort out of a cherry-pick mid-conflict and want to back out cleanly:

```bash
git reset --hard HEAD                       # clear index/worktree; dropping temp branch loses nothing (it pointed at main)
git checkout main && git branch -D <temp>   # then delete the temp branch
```

`git reset --hard` is destructive to uncommitted changes — confirm with the user before issuing it.

---

## Part 2 — Verify a remote is a REAL fork before pushing

A repo with a fork-*like* name is **not necessarily a fork** of the repo you think. It can be a config/notes repo, a renamed project, or a personal snapshot. Pushing source commits there either rewrites its history (destructive) or dumps unrelated files into it.

### Confirm with the GitHub API (decisive field: `fork` / `parent`)

```bash
curl -s https://api.github.com/repos/$OWNER/$REPO | python3 -c "import sys,json; d=json.load(sys.stdin); print('full_name:',d.get('full_name')); print('fork:',d.get('fork')); print('parent:',(d.get('parent') or {}).get('full_name'))"

# gh equivalent
gh repo view $OWNER/$REPO --json name,isFork,parent --jq '{name, isFork, parent: .parent.name}'
```

### Decision rule

- **`fork: true` AND `parent: <the-upstream-you-expect>`** → genuine fork, safe to push.
- **`fork: false` (or `parent: null`)** → NOT a fork. It is a standalone repo. Pushing main-of-a-different-project there clobbers its history or dumps wrong files. **Stop; do NOT push blindly.** Ask where to push, or confirm before any `git push`.

### Check the local remote config too

```bash
git remote -v
git config --get-regexp '^remote\.'
```

Watch for: `origin` pointing at an upstream you don't own (e.g. `NousResearch/hermes-agent`) — never push there; and a `fork`/other remote whose URL returns `Repository not found` (possibly deleted, renamed, or a name mismatch).

### Repo-inspection cue

A standalone repo that looks unrelated (contains `config.yaml`, `profiles/`, `skills/`, `SOUL.md`, `state/`, `plans/`) is a *configuration* repo, not a source fork. If the user calls it "my fork" of a source project, surface the mismatch and confirm the destination before pushing.

---

## Pitfalls

- Don't trust `git status` alone — a clean status does not prove the user's work is safe. Check reflog + `fsck --unreachable` when work seems missing.
- Don't `git cherry-pick -X ours`/`theirs` and assume you got the user's intent. Diff the staged file vs the source blob for redesigned files.
- Don't push into an unverified remote. Confirm `fork: true` + correct `parent` first, or stop.
- `git reset --hard` and `git branch -D` are destructive — confirm before running.
- If the push destination is genuinely absent (deleted fork, wrong name), do not create a fork or pick a remote without the user naming the right place.
