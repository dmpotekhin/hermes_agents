# Triage of a `scan_credentials.py` hit

`CREDENTIAL PATTERN(S) DETECTED` is a candidate, not a confirmed leak. The scanner matches the
header line of a PEM block, and documentation bodies contain those headers legitimately.

## Procedure

1. **Pull context around every match with the base64 masked**, so key material never enters the
transcript:

   ```python
   import re
   raw = open(path, encoding='utf-8', errors='replace').read()
   for m in re.finditer('-----BEGIN', raw):
       seg = raw[m.start()-400:m.start()+700].replace('\\n', '\n')
       print(re.sub(r'([A-Za-z0-9+/]{40,})', lambda x: '<B64 len=%d>' % len(x.group(1)), seg))
   ```

2. **Documentation, not a key** — the usual case in a large generated body (agent rosters,
   cheatsheets, SKILL.md examples):
   - The hit sits inside a JSON string / markdown body that *describes* secrets, e.g. a SecOps
     agent's instructions listing the patterns a scanner should look for.
   - The header appears with no key body, or the body is broken by `\n` literals.
   - Several headers of different key types (RSA, EC, PGP) cluster in one paragraph.
   Verdict: a false positive. Say so explicitly in the report and continue; do not rename,
   delete or obfuscate the file to silence the scanner.

3. **Real key** — a header with a plausible base64 body and no surrounding prose:
   hard STOP, do not commit, show the user file + line, rotate the key. If it is already in
   git history, the fix is rotation plus history rewrite, not a new commit that removes it.

## Notes

- Files above ~1 MB (rosters, dumps) produce nearly all textual hits — read context before
  judging by pattern name.
- `--staged` is documented to exit `1` on a finding; verify the exit code WITHOUT a pipe,
  otherwise `$?` is `tail`'s status and a finding looks like success.
- Scan again after unstaging junk (`db-shm` etc.) — the index changed, so the previous verdict
  no longer describes the commit you are about to make.
