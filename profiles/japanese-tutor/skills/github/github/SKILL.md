---
name: github
description: "Complete GitHub workflow: auth, issues, PR lifecycle, code review, repo management. One umbrella for all GitHub interaction."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Authentication, Issues, Pull-Requests, Code-Review, Repositories, CI/CD, Git]
    category: github
---

# GitHub — Complete Workflow Umbrella

This skill covers all aspects of interacting with GitHub: authentication, issue management, pull request lifecycle, code review, and repository management. Pick the section you need.

## Prerequisites: Auth Detection (shared by all sections)

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\\n\\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\\([^@]*\\)@.*|\\1|')
    fi
  fi
fi

REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -n "$REMOTE_URL" ]; then
  OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\\.com[:/]||; s|\\.git$||')
  OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
  REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
fi
```

---

## Section 1: Authentication Setup

Set up GitHub access via HTTPS tokens or SSH keys, and configure gh CLI.

### Git-Only Auth (HTTPS with Personal Access Token)
```bash
git config --global credential.helper store
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git ls-remote https://github.com/<username>/<any-repo>.git
```

### Git-Only Auth (SSH)
```bash
ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
ssh -T git@github.com
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### gh CLI Auth
```bash
gh auth login
echo "<token>" | gh auth login --with-token
gh auth setup-git
```

---

## Section 2: Issue Management

```bash
gh issue list --state open --label "bug"
gh issue create --title "Bug: ..." --body "## Description\n..." --label "bug"
gh issue edit 42 --add-label "priority:high" --add-assignee username
gh issue close 42 --reason "completed"
gh issue comment 42 --body "Working on a fix."
```

---

## Section 3: PR Workflow

```bash
git checkout -b feat/description
git add <files> && git commit -m "feat: ..."
git push -u origin HEAD

gh pr create --title "feat: ..." --body "## Summary\n..." --label "enhancement"
gh pr checks --watch
gh pr merge --squash --delete-branch
```

---

## Section 4: Code Review

```bash
git diff main...HEAD --stat
gh pr checkout 123
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."
```

---

## Pitfall: GitHub auth on a fresh macOS

If `gh` is not installed (macOS default), use SSH directly:

```bash
# Check if SSH key exists
test -f ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519 -C "$(git config user.email)" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub   # add to github.com/settings/keys
ssh -T git@github.com
git remote set-url origin git@github.com:owner/repo.git
```

## Reference: Hermes config backup to GitHub

See `references/hermes-backup-to-github.md` for a full guide on pushing
`~/.hermes/` (profiles, skills, config) to a private repo with a tuned
.gitignore that excludes secrets, sessions, caches, and runtime state.

## Section 5: Repository Management

```bash
gh repo create my-project --public --clone
gh repo fork owner/repo --clone
gh repo edit --description "Updated" --visibility public
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh secret set API_KEY --body "your-secret-value"
gh workflow list
gh run list --limit 10
gh run rerun <RUN_ID> --failed
```
