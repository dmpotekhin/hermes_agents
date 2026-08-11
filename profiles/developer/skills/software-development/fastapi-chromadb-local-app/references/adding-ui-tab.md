# Adding a UI Tab to RAG Assistant

Pattern for adding a new tab (e.g., Prompts) to the RAG Assistant vanilla JS web UI.

## Files to modify

1. `static/index.html` — three changes
2. `static/app.js` — three changes

## Step 1: Add nav button (index.html)

Add a `<button>` in the `<nav>` block:

```html
<button onclick="switchTab('prompts')">Prompts</button>
```

The first tab keeps `class="active"`, others don't.

## Step 2: Add tab content div (index.html)

Insert a `<div id="tab-<name>" class="tab">` before the next tab:

```html
<div id="tab-prompts" class="tab">
  <h2>Prompts</h2>
  <div class="form-row" id="add-prompt-form">
    <input id="prompt-text" placeholder="Prompt text" style="flex:3">
    <input id="prompt-desc" placeholder="Description" style="flex:2">
    <input id="prompt-tags" placeholder="Tags: python, review" style="flex:1">
    <button onclick="addPrompt()">Add</button>
  </div>
  <table id="prompts-table">
    <thead><tr><th>Description</th><th>Text</th><th>Tags</th><th></th></tr></thead>
    <tbody></tbody>
  </table>
  <div id="prompts-empty" class="empty" style="display:none">No prompts yet.</div>
</div>
```

Fields to customize: tab id, form-row id, input ids, table id, empty div id, button onclick, column headers.

## Step 3: Add tab routing (app.js)

Add to `switchTab()`:

```js
if (name === 'prompts') loadPrompts();
```

## Step 4: Add CRUD functions (app.js)

Three functions: `loadPrompts()`, `addPrompt()`, `deletePrompt(id)`.

**loadPrompts** — fetches `GET /api/<plural>`, renders table rows:

```js
async function loadPrompts() {
  try {
    const prompts = await api('GET', '/api/prompts');
    const tbody = document.querySelector('#prompts-table tbody');
    const empty = document.getElementById('prompts-empty');
    tbody.innerHTML = '';
    if (prompts.length === 0) { empty.style.display = 'block'; return; }
    empty.style.display = 'none';
    prompts.forEach(p => {
      const tags = p.tags.length ? p.tags.map(t => `<span class="badge">${h(t)}</span>`).join(' ') : '-';
      tbody.innerHTML += `<tr>
        <td>${h(p.description)}</td>
        <td>${h(truncate(p.text, 60))}</td>
        <td>${tags}</td>
        <td class="actions">
          <button class="danger" onclick="deletePrompt('${p.id}')">Del</button>
        </td>
      </tr>`;
    });
  } catch (e) { console.error(e); }
}
```

**addPrompt** — reads form inputs, POSTs, clears form, reloads:

```js
async function addPrompt() {
  const text = document.getElementById('prompt-text').value.trim();
  const description = document.getElementById('prompt-desc').value.trim();
  const tagsStr = document.getElementById('prompt-tags').value.trim();
  const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];
  if (!text || !description) return alert('Text and Description are required');
  try {
    await api('POST', '/api/prompts', { text, description, tags });
    document.getElementById('prompt-text').value = '';
    document.getElementById('prompt-desc').value = '';
    document.getElementById('prompt-tags').value = '';
    loadPrompts();
  } catch (e) { alert('Error: ' + e.message); }
}
```

**deletePrompt** — confirms, DELETEs, reloads:

```js
async function deletePrompt(id) {
  if (!confirm('Delete this prompt?')) return;
  await api('DELETE', '/api/prompts/' + id);
  loadPrompts();
}
```

## CSS classes available (from index.html `<style>`)

- `.badge` — tag pill
- `.danger` — red button (delete)
- `.secondary` — dark button
- `.actions` — flex row for button group
- `.empty` — centered muted text for empty state
- `.form-row` — horizontal form with gap

## Verification

After changes, refresh the browser. The server's StaticFiles middleware serves updated files from disk (no restart needed). Verify: `curl -s http://localhost:8765/ | grep "Prompts"` should return matches.
