# Brain MCP — Complete Tool Catalog

14 tools available via MCP. All operate on `Brain/` inside the Obsidian vault.

## brain_feedback
Record a taste signal from user interaction.
- **topic** (required): Normalized slug (lowercase, hyphens)
- **sign** (required): `positive` | `negative`
- **principle** (required): The rule expressed
- **agent** (required): Agent name
- **scope** (optional): `coding` | `communication` | `writing` | `general`
- Stores: `Brain/inbox/sig-YYYY-MM-DD-{topic}-{hash}.md`

## brain_apply_evidence
Record whether a preference was applied or violated.
- **pref_id** (required): e.g. `pref-no-abbrev`
- **result** (required): `applied` | `violated` | `outdated`
- **context** (optional): Explanation

## brain_dream
Run the deterministic rule engine. Idempotent.
- **dry_run** (optional): Preview without writing

## brain_context
Read confirmed + quarantined preferences. No params.

## brain_context_pack
Budgeted context slice within token limit.
- **max_tokens** (required): Token budget

## brain_search
FTS5 full-text search over vault.
- **query** (required): Search terms
- **limit** (optional): Max results (default 20)

## brain_status
Vault status: path, config, counts, last dream. No params.

## brain_audit
Log history for a preference.
- **pref_id** (required): Preference ID

## brain_rollback
Restore most recent snapshot. No params.

## brain_health
Health check: verdict + domain-level diagnostics. No params.

## brain_hygiene
Scan for near-duplicates and stale signals.
- **scan** (optional): Run scan (default true)

## brain_obligation
Manage recurring obligations.
- **operation** (required): `add` | `done` | `list` | `show` | `remove`
- **title**: Obligation title (required for add)
- **cadence**: `daily` | `weekly` | `biweekly` | `monthly` | `quarterly` | `yearly` | `every-N-days`

## brain_create_note
Create markdown in Brain/notes/.
- **path** (required): Relative path, must end with `.md`
- **frontmatter** (optional): Key-value YAML frontmatter
- **content** (optional): Markdown body

## brain_devlog
Append timestamped entry to dev journal.
- **entry** (required): Log line text
- **project** (optional): Project tag for grouping
- Writes: `Brain/journal/YYYY-MM-DD.md` (creates if needed)
- Format: `HH:MM | project:name | entry text`
