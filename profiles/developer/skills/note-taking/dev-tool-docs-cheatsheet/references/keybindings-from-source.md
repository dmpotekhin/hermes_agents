# Keybindings / hotkeys cheatsheet — ground truth is the tool's source

When the deliverable is a HOTKEYS / keyboard-shortcut cheatsheet for a tool INSTALLED on this machine, do not invent shortcuts or trust memory/secondary docs. The real map lives in the tool's own code. Find it, quote it verbatim, then note the platform modifier.

## Locating the real keybinding map

```bash
# 1. Find the tool's install/source dir (Hermes example:)
#    ~/.hermes/hermes-agent/          (git-installed source)
#    Search for the keybinding/hotkey source:
#    search_files pattern='hotkey|key_bindings|keybindings|KEY_BIND' target='files'
```

High-value search patterns (in source):
- `hotkeys.ts` / `hotkey` (UI framework hotkey definitions)
- `keybindings.json`, `key_bindings`, `KEY_BIND`, `keybinding`
- `cmd+`, `ctrl+`, `CommandOrControl`, `accelerator` (desktop apps)
- `HOTKEYS`, `shortcut` arrays / tables
- README files often carry a canonical keybindings table (`README.md`)

## Crucially — platform modifier

Keybinding files usually branch on OS: `const action = isMac ? 'Cmd' : 'Ctrl'`. Always state this in the cheatsheet (macOS = Cmd, Linux/Windows = Ctrl). Also call out editor-specific swallow: e.g. in VS Code/Cursor `Cmd+G` is bound to Find Next, so the tool's default `Cmd+G` must fall back to `Alt+G`.

## Verification for a hotkeys cheatsheet

- Every shortcut must trace to a source line (comment with the file path, or a source link in the note).
- Grep the finished note for `TODO|TBD|PLACEHOLDER|FIXME` — expect none.
- Confirm the file landed (test -f) and, if the tool is named, grep the note for the tool name.

## Why this beats docs/memory
Keybinding docs lag versions and secondary blogs paraphrase. The installed source is the single version of truth for the keyboard interface the user will actually hit.
