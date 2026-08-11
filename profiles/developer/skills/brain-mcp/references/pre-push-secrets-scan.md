# Pre-Push Secrets Scan

Run before pushing any project to a public GitHub repository.

## Automated scan

```bash
cd /path/to/project

# 1. Scan for API keys, tokens, passwords
grep -rnE '(API_KEY|TOKEN|SECRET|PASSWORD|api_key|token|secret|password|credential)\s*[:=]\s*["'"'"']?\w{8,}' \
  --include='*.ts' --include='*.json' --include='*.yaml' --include='*.yml' \
  --include='*.md' --include='*.sh' --include='*.py' --include='*.env' . \
  2>/dev/null | grep -v node_modules | grep -v '.git/' | grep -v bun.lock

# 2. Scan for personal paths (/Users/, /home/)
grep -rn '/Users/\|/home/' . \
  --include='*.ts' --include='*.json' --include='*.md' --include='*.sh' \
  --include='*.yaml' --include='*.yml' --include='*.py' \
  2>/dev/null | grep -v node_modules | grep -v '.git/'

# 3. Scan for email addresses
grep -rnE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' . \
  --include='*.ts' --include='*.json' --include='*.md' --include='*.sh' \
  2>/dev/null | grep -v node_modules | grep -v '.git/'

# 4. Check bin/launcher scripts for hardcoded paths
find . -type f \( -name '*.sh' -o -path '*/bin/*' \) -exec grep -l '/Users/\|/home/' {} \;

# 5. Check git history for accidentally committed secrets
git log -p | grep -iE '(api.key|token|password|secret|credential|/Users/)' | head -20
```

## Common issues found

| Issue | Example | Fix |
|-------|---------|-----|
| Hardcoded home path in bin script | `BRAIN_VAULT="/Users/me/Vault"` | Use env var or relative paths |
| Hardcoded project path in docs/specs | `cd /Users/me/project` | Replace with `~/project` or placeholder |
| IDE config tracked (.idea/) | `.idea/vcs.xml` committed | Add `.idea/` to `.gitignore` |
| Internal dev artifacts | `.superpowers/sdd/` task briefs | Add to `.gitignore` or remove |
| Example config with real paths | `vault_path: /Users/me/...` | Replace with `/path/to/vault` |

## .gitignore template for TypeScript/Bun projects

```
node_modules/
dist/
*.log
.DS_Store
.idea/
.superpowers/
```

## Pitfall: Hermes internal dev directories

Hermes agent creates `.superpowers/` with task briefs during development. These contain real filesystem paths and should NEVER be pushed to public repos. Always add to `.gitignore` before initial commit.
