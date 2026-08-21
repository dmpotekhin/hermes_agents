# macOS temp-file quirks for hermes-verify- scripts

Observed while satisfying the verification tracker after a code edit.

## `mktemp -t` does NOT substitute the `XXXXXX` runes on macOS

`mktemp -t hermes-verify-editor.XXXXXX.sh` creates a file literally NAMED
`hermes-verify-editor.XXXXXX.sh` — the runes stay verbatim (BSD mktemp treats the
whole `-t` value as a prefix template differently from GNU). The verification
tracker keys on the `hermes-verify-` prefix and the file's real location, so a
literal-XXXXXX name can be treated as unverified.

Correct form — GNU-style template with the explicit temp dir:

```bash
TMPBASE="/private/var/folders/.../T"          # exact dir the tracker expects
VERIFY_FILE=$(mktemp "$TMPBASE/hermes-verify-<name>.XXXXXX.sh")
```

Always echo/confirm the printed path has no literal `XXXXXX` before running the
script, and `rm -f` it after the run.

## The tracker wants the script created via mktemp and cleaned up

Pattern that satisfies the verification-before-completion tracker after a code
edit:

1. `mktemp "$TMPBASE/hermes-verify-<name>.XXXXXX.sh"` (explicit template, exact TMPDIR).
2. Write the verification body (typecheck / grep for old+new expressions / assertions).
3. Run it, capture `rc`.
4. `rm -f "$VERIFY_FILE"` and report `rc=0` as green.

Note: the tracker may still flag "unverified" if the FIRST attempt used the broken
`-t` form — re-run with the correct mktemp form and confirm the clean-up line
printed `yes` before reporting done.
