# Excel edits that never reached disk

Scenario: user says «я удалил в таблице дубли / я обновил таблицу», git shows the repo
`Книги.xlsx` clean, and you're asked to push. The rebuild/push is a no-op unless the file
on disk actually changed.

## Diagnose in this order (all read-only)

1. `stat -f "%Sm %z" Книги.xlsx` (macOS) — old mtime + clean `git status --short` =
   the edit never hit disk.
2. Look for a `~$Книги.xlsx` lock file in the repo dir. Its presence means the workbook
   is OPEN in Excel right now → the user's deletions live only in Excel's memory until
   Cmd+S (Сохранить). Do NOT rebuild or push — ask the user to save and confirm.
3. If the repo copy is unchanged, scan the filesystem for other copies of the table —
   the user may have edited a different file:
   `find ~/Downloads ~/Desktop ~/Documents -name "*.xlsx" -maxdepth 2` (or search_files
   target=files pattern `*.xlsx`). Likely names: `Книги.xlsx`, `Потехин Дмитрий книги.xlsx`,
   `Потехин Дмитрий книги (7).xlsx`, `Потехин Дмитрий книги (8).xlsx`.
4. Compare mtimes and row counts across copies (openpyxl: count non-empty title rows) to
   find the freshest / deduped one. A deduped file has fewer title rows than the repo copy.

## Verified example (2026-08-24)

- Repo `Книги.xlsx`: 548 title rows (4 exact dupes + 1 garbage «ы»), mtime 23:56, git clean.
- User claimed duplicates removed; file on disk unchanged; `~$Книги.xlsx` present → open in
  Excel, edits unsaved. Alternative copies in Downloads were OLDER (446–521 rows, mtimes
  days earlier). Conclusion: nothing to push; asked user to Cmd+S first.

## Rule

Never rebuild/commit/push based on what the user SAYS they edited. Verify the file on disk
(mtime, git status, lock file, copies) first. If the source is unchanged, the task is
"tell the user to save" — not "push".
