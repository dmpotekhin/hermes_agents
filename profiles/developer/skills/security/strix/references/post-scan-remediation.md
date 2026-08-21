# Post-Scan Remediation (Strix against a local target)

Strix's SCA (dependency) findings are NOT auto-fixed; only the dynamically
validated code findings are. This is the follow-through after a run returns
exit code 2 ("vulnerabilities found").

## 1. Review what Strix changed
Strix mounts a local target writable and auto-applies its own remediation
patches to source files. After the run:
- `git status --short` + `git diff --stat` to see what it touched
- `git diff` each file — the fixes are usually correct, but review them
- Common shapes it produces: a SQL query validator (blocklist + single-SELECT
  check), read-only-transaction hardening (`SET TRANSACTION READ ONLY` +
  `statement_timeout`), a role-demotion migration (`db/NN_revoke.sql` with
  `ALTER ROLE ... NOSUPERUSER` + `REVOKE`), a docker-compose mount for that
  migration, and an IDOR guard (reject foreign identity).
- It may also run DB migrations LIVE against the running database (e.g.
  `ALTER ROLE trainer NOSUPERUSER`) — so the "manual step for existing volumes"
  that initdb scripts normally require is often already done. Verify with
  `SELECT current_setting('is_superuser')` rather than assuming.

## 2. Verify the fix live (do not trust "remediated in the codebase")
Strix re-tests its own fixes, but verify independently against the running app.
Start the backend, then assert:
- injection payload → blocked (e.g. `SELECT pg_read_file('/etc/passwd')` → 400)
- multi-statement write payload (`BEGIN TRANSACTION READ WRITE; INSERT ...`) → 400
- legit reference query → still `correct:true` (the feature must not break)
- IDOR: foreign `user_id` → 403; the default/local profile → 200

Write these checks with `curl`, not Python `urllib` — urllib can time out on
localhost in the Hermes sandbox where curl succeeds. A `hermes-verify-*.sh`
script of `curl -s -o /dev/null -w "%{http_code}"` assertions is reliable.

## 3. Dependency follow-through (SCA findings)
Bump the DIRECT dependency that pins the vulnerable transitive one, not the
transitive itself:
- `starlette` CVE → bump `fastapi` (fastapi pulls the patched starlette)
- `nanoid` DoS → bump `postcss` (postcss pins `nanoid ^3.3.17`)
- `vite` major bump (5→8 is rolldown-based) → bump `@vitejs/plugin-react` to match
Then `npm audit` must read `0 vulnerabilities`, and run the production build.

## 4. Commit
- Run the credential scan before committing; the repo's pre-commit hook
  (gitleaks + bandit) also fires on `git commit`.
- bandit may block on B324 (weak MD5) even for a non-security hash — fix with
  `hashlib.md5(x, usedforsecurity=False)` (Python 3.9+), not `# nosec`.
