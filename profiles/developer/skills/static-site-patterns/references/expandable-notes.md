# Expandable Notes — Full Implementation

Pattern for adding per-item notes to a static HTML/JS site.

## Data: `js/notes-data.js`

```javascript
const bookNotes = {
  "Book Title Exactly Matching data key": {
    "summary": "2-4 sentence summary paragraph.",
    "themes": ["tag1", "tag2", "tag3"]
  }
};
```

Match keys exactly to the title field in the main data array.

## Card rendering: `js/books.js`

In `createBookCard()`:

```javascript
// Check for notes
const hasNotes = typeof bookNotes !== 'undefined' && bookNotes[book.title];

if (hasNotes) {
    card.classList.add('has-notes');
    
    const notesBtn = document.createElement('button');
    notesBtn.className = 'book-notes-btn';
    notesBtn.textContent = '📝 Notes';
    card.appendChild(notesBtn);
    
    const notesPanel = document.createElement('div');
    notesPanel.className = 'book-notes-panel';
    const note = bookNotes[book.title];
    notesPanel.innerHTML = `
        <div class="book-notes-summary">${note.summary}</div>
        <div class="book-notes-themes">
            ${note.themes.map(t => `<span class="book-notes-tag">${t}</span>`).join(' ')}
        </div>
    `;
    card.appendChild(notesPanel);
    
    notesBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        const isOpen = card.classList.toggle('notes-open');
        notesBtn.textContent = isOpen ? '📝 Hide' : '📝 Notes';
    });
}
```

## CSS: `css/styles.css`

```css
.book-card .book-notes-btn {
    display: block; width: 100%;
    margin-top: var(--spacing-sm);
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px dashed var(--accent-primary);
    border-radius: var(--radius-sm);
    background: transparent; color: var(--accent-primary);
    cursor: pointer; font-size: 0.85rem;
    transition: all var(--transition-fast);
}
.book-card .book-notes-btn:hover {
    background-color: var(--accent-primary); color: white;
    border-style: solid;
}

.book-notes-panel {
    max-height: 0; overflow: hidden;
    transition: max-height 0.35s ease, padding 0.35s ease;
    padding: 0 var(--spacing-sm); margin-top: 0;
}
.book-card.notes-open .book-notes-panel {
    max-height: 600px; padding: var(--spacing-sm);
    margin-top: var(--spacing-sm); overflow-y: auto;
}

.book-notes-summary {
    font-size: 0.85rem; line-height: 1.5;
    color: var(--text-primary); margin-bottom: var(--spacing-sm);
}
.book-notes-themes { display: flex; flex-wrap: wrap; gap: 4px; }
.book-notes-tag {
    display: inline-block; font-size: 0.7rem;
    padding: 2px 8px; border-radius: 10px;
    background-color: var(--bg-tertiary); color: var(--text-secondary);
    border: 1px solid var(--border-color);
}
```

## Script order in HTML

```html
<script src="js/books-data.js"></script>
<script src="js/notes-data.js"></script>   <!-- AFTER data, BEFORE render logic -->
<script src="js/books.js"></script>
```
