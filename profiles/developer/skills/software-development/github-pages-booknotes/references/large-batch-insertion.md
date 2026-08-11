# Large-Batch Notes Insertion Script

When 20+ books need notes, parallelize generation via `delegate_task` (3 groups, ~15 books each),
then combine and insert with this pattern.

## Insertion script (`_insert_all.py`)

```python
"""Insert book notes from multiple JSON files into notes-data.js"""
import json, re

REPO = '/Users/dmitrypotekhin/Downloads/dmpotekhin.github.io'

# Load existing notes-data.js
with open(f'{REPO}/js/notes-data.js') as f:
    content = f.read()

# Load all group JSONs (adjust paths)
groups = [
    'book_notes_group1.json',
    'book_notes_group2.json',
    'book_notes_group3.json',
]
all_new = {}
for g in groups:
    with open(g) as f:
        all_new.update(json.load(f))

# Build insertion block
insertions = []
for title, note in all_new.items():
    escaped = title.replace('"', '\\"')
    entry = f'\n  "{escaped}": {json.dumps(note, ensure_ascii=False, indent=4)}'
    insertions.append(entry)

# Insert before closing }; — only ONE }; should remain
combined = ',\n'.join(insertions)
content = content.replace('\n};', f'{combined}\n}};')

with open(f'{REPO}/js/notes-data.js', 'w') as f:
    f.write(content)

# Verify
note_keys = re.findall(r'^\s{2}"([^"]+)": \{', content, re.MULTILINE)
print(f'Total notes after insertion: {len(note_keys)}')
```

## Run
```bash
cd /Users/dmitrypotekhin/Downloads/dmpotekhin.github.io
python3 _insert_all.py
```

## Pitfalls
- `write_file` on notes-data.js silently fails for large files (>500KB). Always use a Python script with `open(... 'w')`.
- Ensure NO double commas: the insertion replaces `\n};` with `{entries}\n};` — the last entry gets no trailing comma.
- Verify with Python regex, not `node -e` (blocked).
