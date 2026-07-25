---
name: hermes-plugins
description: "Install, configure, and troubleshoot Hermes Agent plugins — cloning from repos, wiring config.yaml, and avoiding common pitfalls."
version: 1.0.0
---

# Hermes Agent Plugin Installation

Installing third-party plugins into Hermes Agent. Covers the full lifecycle: cloning, copying files, configuring, and verifying.

## When to Use

- Installing a plugin from a GitHub repo (image_gen, toolsets, platform adapters, etc.)
- Configuring `custom_providers`, `plugins.enabled`, or plugin-specific config sections
- User says "install this Hermes plugin from <url>"

## Prerequisites

- Hermes Agent installed and the target profile active
- Plugin repo URL (GitHub, public)
- Any API keys the plugin needs

## Workflow

### 1. Clone the Repo

Clone to `/tmp` to inspect structure before committing to the plugins directory:

```bash
git clone <repo-url> /tmp/<repo-name>
```

Inspect the plugin directory — look for `plugin.yaml` (manifest), `__init__.py` (register function), and submodules.

### 2. Copy Plugin Files

Plugins live under `~/.hermes/plugins/<category>/<name>/`. The `<category>` depends on the plugin kind:

| Plugin kind | Target path |
|---|---|
| `image_gen` backend | `~/.hermes/plugins/image_gen/<name>/` |
| Toolset plugin | `~/.hermes/plugins/<toolset>/<name>/` |
| Platform adapter | `~/.hermes/plugins/platforms/<name>/` |

```bash
mkdir -p ~/.hermes/plugins/<category>
cp -r /tmp/<repo-name>/<plugin_dir> ~/.hermes/plugins/<category>/<name>/
```

### 3. Configure via `hermes config set`

**CRITICAL PITFALL**: Do NOT use `patch` or `write_file` on `config.yaml`. Hermes protects its config file — direct edits are refused with "Refusing to write to Hermes config file."

**CRITICAL PITFALL #2**: `hermes config set` silently **stringifies** array and object values for unrecognized keys. Setting `plugins.enabled '["image_gen/abacus_ai"]'` produces `plugins:\n  enabled: '["image_gen/abacus_ai"]'` — a string literal, NOT a YAML list. The plugin won't be found because Hermes sees a string where it expects a list. `--force` does NOT fix type coercion — it only suppresses the unrecognized-key warning.

**THE FIX**: Use `hermes config edit` with a custom `EDITOR` script to write properly-typed YAML. See `references/config-array-pitfall.md` for the reusable fix script and detailed explanation.

#### Enable the plugin

First, set scalar keys directly (these work fine):
```bash
hermes config set <category>.provider <name>
hermes config set <category>.<name>.setting value
```

Then, for arrays/objects (`plugins.enabled`, `custom_providers`), use the `hermes config edit` + EDITOR workaround from `references/config-array-pitfall.md`. Quick version:

```bash
# 1. Set a temporary placeholder (so the key exists)
hermes config set --force plugins.enabled placeholder

# 2. Fix the type via hermes config edit with a Python EDITOR script
#    (see references/config-array-pitfall.md for the full reusable script)
EDITOR=/tmp/fix_config.py hermes config edit
```

#### Add custom_providers (API keys)

Same approach as above — set a placeholder, then fix via the EDITOR script pattern.

#### Unrecognized key warning

When you set keys not in Hermes's built-in schema (like `image_gen.provider`, `plugins.enabled`), you'll see:

```
⚠ '<key>' is not a recognized config key — it was saved anyway, but Hermes may not read it.
```

This is normal for plugin config and harmless for **scalar** values. For arrays/objects, this is a red flag — the value may have been stringified. Verify with `hermes config` and use the EDITOR workaround if needed.

### 4. Restart

Gateway users:
```bash
hermes gateway restart
```

CLI-only users: start a new session (`/reset` in interactive mode, or exit and relaunch).

### 5. Verify

Check the plugin is recognized:
```bash
hermes plugins list
```

Check the config took effect:
```bash
hermes config | grep -A5 <category>
```

## Common Pitfalls

### Config changes not taking effect

Plugin and toolset changes require a session reset (`/reset`) or gateway restart. They do NOT apply mid-conversation.

### "Not a recognized config key" warning

Harmless for plugin keys. Hermes saves the value anyway. Plugin config sections (`image_gen.provider`, `plugins.enabled`, etc.) are custom keys the plugin reads at startup.

### Forgot to set the API key

The plugin's config resolver typically checks both `custom_providers` in config.yaml AND environment variables. If neither has the key, `is_available()` returns false and the plugin silently won't work. Check with:
```bash
hermes plugins list
```

### Gateway not running for current profile

`hermes gateway restart` only affects the active profile. Other profiles are independent. Check profile first:
```bash
hermes profile show
```

### Delegation model not using custom_providers

Setting `delegation.provider: abacus-ai` does NOT automatically inherit `base_url` and `api_key` from `custom_providers`. If delegation calls fail with auth errors, set `delegation.base_url` and `delegation.api_key` explicitly:

```bash
hermes config set delegation.base_url "https://routellm.abacus.ai/v1"
hermes config set delegation.api_key "s2_YOUR_KEY"
```

Alternatively, `delegation` has dedicated `base_url` and `api_key` fields that take precedence over custom_providers lookup. Test delegation with a simple task before relying on it for production work.

## Example: Installing Abacus AI Image Gen Plugin

See `references/abacus-ai-example.md` for the full step-by-step with this specific plugin.
