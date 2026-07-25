---
name: japanese-text-processing
description: Set up kuroshiro + kuromoji in Vite/React for automatic furigana, dictionary lookup via jisho.org, and Web Speech API TTS. Covers Vite config pitfalls, CJS polyfills, dict file serving, and CSS-only furigana toggle patterns.
---

# Japanese Text Processing in Vite + React

Set up a Japanese reading app with automatic furigana (ruby annotations), dictionary lookup, and text-to-speech — all in the browser.

## Dependencies

```bash
npm install kuroshiro kuroshiro-analyzer-kuromoji react-router-dom zustand
npm install path-browserify
```

## Vite Configuration — The Critical Parts

kuromoji is a CJS module that uses Node.js APIs (`path.join`, `fs`). It also loads `.dat.gz` dictionary files. Vite needs:

```ts
// vite.config.ts
import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

function kuromojiDictPlugin(): Plugin {
  return {
    name: 'kuromoji-dict',
    configureServer(server) {
      // CRITICAL: Serve .dat.gz as raw binary WITHOUT content-encoding.
      // Vite's default compression middleware double-gzips these files,
      // and kuromoji's BrowserDictionaryLoader decompresses client-side.
      server.middlewares.use((req, res, next) => {
        if (req.url?.endsWith('.dat.gz')) {
          const filePath = path.join(server.config.root, 'public', req.url)
          if (fs.existsSync(filePath)) {
            const stat = fs.statSync(filePath)
            res.writeHead(200, {
              'Content-Type': 'application/octet-stream',
              'Content-Length': stat.size,
              'Cache-Control': 'no-cache',
            })
            fs.createReadStream(filePath).pipe(res)
            return
          }
        }
        next()
      })
    }
  }
}

export default defineConfig({
  plugins: [react(), kuromojiDictPlugin()],
  resolve: {
    alias: {
      'path': 'path-browserify',  // polyfill for kuromoji's Node path
    }
  },
  define: {
    'process.env': '{}',
    'global': 'globalThis'
  },
  assetsInclude: ['**/*.dat', '**/*.dat.gz'],
  server: {
    proxy: {
      '/jisho': {
        target: 'https://jisho.org',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/jisho/, '')
      }
    }
  }
})
```

### Why this config is necessary

- **path-browserify**: kuromoji's DictionaryLoader calls `path.join(dic_path, "base.dat.gz")`. Without this polyfill, it crashes.
- **process.env / global**: kuromoji checks these for Node.js environment detection.
- **Custom middleware**: Vite's dev server applies `content-encoding: gzip` to `.gz` files. The browser auto-decompresses, and kuromoji's zlib decompressor gets corrupted data → "invalid file signature" errors.
- **assetsInclude**: Makes Vite treat `.dat` and `.dat.gz` files as static assets.

### Dictionary files

The copy script must handle the `.gz` files:

```json
"scripts": {
  "copy-dict": "mkdir -p public/dict && cp -r node_modules/kuromoji/dict/* public/dict/",
  "predev": "npm run copy-dict",
  "dev": "vite"
}
```

## Kuroshiro Initialization — Race Condition Fix

```ts
// hooks/useKuroshiro.ts
let kuroshiroInstance: Kuroshiro | null = null
let initPromise: Promise<Kuroshiro> | null = null

function getKuroshiro(): Promise<Kuroshiro> {
  if (kuroshiroInstance) return Promise.resolve(kuroshiroInstance)
  if (initPromise) return initPromise
  initPromise = (async () => {
    const k = new Kuroshiro()
    await k.init(new KuromojiAnalyzer({ dictPath: '/dict' }))
    kuroshiroInstance = k
    return k
  })()
  return initPromise
}
```

**CRITICAL**: Separate `loading` (init started) from `ready` (instance available). In React Strict Mode, effects fire twice. The `convert` function accesses `instanceRef.current` — if you call it before init resolves, it throws "Kuroshiro not initialized".

```ts
// In the hook:
const [loading, setLoading] = useState(true)
const [ready, setReady] = useState(false)  // ← separate state!

// In the .then() handler:
instanceRef.current = k
setLoading(false)
setReady(true)

// In the component:
const { convert, loading, ready, error } = useKuroshiro()

useEffect(() => {
  if (ready) {  // ← guard with ready, not just !loading
    doConvert()
  }
}, [doConvert, ready])
```

## Post-Processing: Adding data-kanji Attributes

kuroshiro outputs `<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>` — no data attributes. For click handling and CSS-based known-kanji hiding, add them:

```ts
let result = await convert(text)
result = result.replace(
  /<ruby>([^<]+)/g,
  '<ruby data-kanji="$1">$1'
)
```

## CSS-Only Furigana Toggle

Never re-render for furigana show/hide — use CSS:

```css
/* Global toggle */
.hide-furigana rt { visibility: hidden; }

/* Per-kanji hiding via dynamic <style> injection */
.known-kanji-mode [data-kanji="公園"] rt { visibility: hidden; }
```

Toggle by adding/removing `.hide-furigana` class on the container. Known kanji styles are injected as a `<style>` block (computed from the store's `knownKanji[]` array).

## Click Delegation

Attach one click handler to the container, not individual `<ruby>` elements:

```ts
container.addEventListener('click', (e) => {
  const ruby = (e.target as HTMLElement).closest('ruby')
  if (!ruby) return
  const kanji = ruby.getAttribute('data-kanji')
  const reading = ruby.querySelector('rt')?.textContent || ''
  if (kanji) onWordClick(kanji, reading)
})
```

## jisho.org Dictionary Lookup

Fetch through Vite proxy (avoids CORS):

```ts
const res = await fetch(`/jisho/api/v1/search/words?keyword=${encodeURIComponent(kanji)}`)
const json = await res.json()
const entry = json.data?.[0]
const reading = entry?.japanese?.[0]?.reading
const definitions = (entry?.senses?.[0]?.english_definitions || []).slice(0, 5)
```

jisho.org is free, no API key, no registration.

## Web Speech API — Fallback Pattern

Some browser/OS combinations don't fire `onboundary` for Japanese. Always wrap in try/catch:

```ts
utterance.onboundary = (e) => {
  try {
    if (e.charIndex !== undefined && e.charIndex >= 0) {
      setCurrentCharIndex(e.charIndex)
    }
  } catch {
    // Silently ignore — playback continues without highlighting
  }
}
```

## Node.js Version

kuromoji and Vite 5 require Node ≥ 18. If the system has an older Node (e.g., 14), use nvm:

```bash
nvm use 20
```

## TypeScript Declarations

kuroshiro and kuroshiro-analyzer-kuromoji lack type definitions. Create `src/types/kuroshiro.d.ts`:

```ts
declare module 'kuroshiro' {
  export default class Kuroshiro {
    constructor()
    init(analyzer: any): Promise<void>
    convert(text: string, options?: { mode?: string; to?: string }): Promise<string>
  }
}

declare module 'kuroshiro-analyzer-kuromoji' {
  export default class KuromojiAnalyzer {
    constructor(options?: { dictPath?: string })
    init(options?: any): Promise<void>
    parse(text: string): Promise<any>
  }
}
```

## Word-Level Pronunciation (Popup)

When showing a dictionary popup for a clicked word, add a 🔊 button using Web Speech API directly (not via the main useSpeech hook):

```tsx
const [speaking, setSpeaking] = useState(false)

const handleSpeak = () => {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(kanji)
  utterance.lang = 'ja-JP'
  utterance.rate = 0.8
  utterance.onstart = () => setSpeaking(true)
  utterance.onend = () => setSpeaking(false)
  utterance.onerror = () => setSpeaking(false)
  window.speechSynthesis.speak(utterance)
}

// In JSX, next to the kanji display:
<button onClick={handleSpeak} disabled={speaking}>
  {speaking ? '⏳' : '🔊'}
</button>
```

Cancel any in-progress utterance first to avoid queuing multiple words.

## Large Text Libraries — Assembly Pattern

When generating many texts (e.g., 125 texts across 25 topics × 5 levels), write them in batches to `/tmp/` files, then assemble with a Python script using `json.dump()` — this handles Unicode escaping correctly. Writing raw JSON with unescaped ASCII quotes (`"I love you"`) inside Japanese content strings will produce invalid JSON.

## Topic Categories

For JLPT-graded reading practice, 25 topic categories from the japanese-tutor vocabulary database:

→ `references/25-topics.md` — Full list with word counts per topic.

## Kanji Stroke Order Trainer Integration

Embed a kanji stroke order trainer (from [kanji-trainer](https://github.com/dmpotekhin/kanji-trainer)) in the word popup using iframes with `?kanji=` URL parameter.

### Copy and Adapt the Trainer

The kanji-trainer is a single `index.html` file (pure HTML+CSS+JS, no dependencies). Copy it to `public/kanji-trainer.html` and add auto-load support:

```html
<!-- Add right before render() in the init section -->
<script>
// Auto-load kanji from URL parameter ?kanji=
const params = new URLSearchParams(window.location.search);
const kanjiParam = params.get('kanji');
if (kanjiParam && [...kanjiParam].length === 1) {
  input.value = kanjiParam;
  loadKanji(kanjiParam);
}
</script>
```

For embedding, make the background transparent (the trainer's body has `background: #1a1a2e` — change to `background: transparent`).

### Extract Kanji Characters from a Word

Use a Unicode range regex to filter kana and get only kanji:

```ts
function extractKanjiChars(text: string): string[] {
  return [...text].filter((ch) => /[\u4e00-\u9faf\u3400-\u4dbf]/.test(ch))
}
// extractKanjiChars("公園") → ["公", "園"]
// extractKanjiChars("祖母") → ["祖", "母"]
// extractKanjiChars("する") → []
```

### Embed in WordPopup

Add a toggle button and a grid of iframes — one per kanji character:

```tsx
const [showStrokeOrder, setShowStrokeOrder] = useState(false)
const kanjiChars = extractKanjiChars(kanji)

// Reset when word changes
useEffect(() => { setShowStrokeOrder(false) }, [kanji])

// Toggle button
<button onClick={() => setShowStrokeOrder(!showStrokeOrder)}>
  ✏️ Stroke Order {showStrokeOrder ? '▲' : '▼'}
</button>

// Iframes in a responsive grid
{showStrokeOrder && kanjiChars.length > 0 && (
  <div className={`grid gap-2 ${kanjiChars.length > 1 ? 'grid-cols-2' : 'grid-cols-1'}`}>
    {kanjiChars.map((ch, i) => (
      <div key={i}>
        <div>{ch}</div>
        <iframe
          src={`/kanji-trainer.html?kanji=${encodeURIComponent(ch)}`}
          style={{ height: '340px', border: 'none' }}
        />
      </div>
    ))}
  </div>
)}
```

**Important:** Make the popup wider when stroke order is expanded (`max-w-lg` instead of `max-w-xs`) and adjust `top`/`left` positioning to prevent overflow.

### How it works

1. User clicks a word → WordPopup opens with dictionary data
2. User clicks "Stroke Order" → kanji characters are extracted, iframes load `/kanji-trainer.html?kanji=公` etc.
3. Each iframe auto-loads the specified kanji from KanjiVG (fetches SVG from `raw.githubusercontent.com/KanjiVG/kanjivg`)
4. User can step through strokes (◀▶), use autoplay with speed control, or keyboard arrows

The trainer has no dependencies and works entirely in the browser. KanjiVG data is fetched per-request (requires internet).

## Custom Text Reader Pattern

When users paste their own Japanese text, store it properly and show it with all the same features:

### Storage Split: localStorage + sessionStorage

- **localStorage** → metadata list (`[{id, title, content, createdAt}]`), max 20 entries, content truncated to preview length
- **sessionStorage** → full content per text (key: `custom-content-{id}`), up to 25 000 chars
- Rationale: localStorage has ~5MB limit, sessionStorage is per-tab and auto-cleared

```ts
const MAX_TEXTS = 20
export const MAX_CHARS_PER_TEXT = 25_000

function saveFullContent(id: string, content: string) {
  const trimmed = content.slice(0, MAX_CHARS_PER_TEXT)
  sessionStorage.setItem(`custom-content-${id}`, trimmed)
}
```

### Character Counter UX

```tsx
const charCount = content.length
const overLimit = charCount > MAX_CHARS_PER_TEXT

const getCharColor = () => {
  if (charCount > MAX_CHARS_PER_TEXT) return '#ef4444'        // red — over limit
  if (charCount > MAX_CHARS_PER_TEXT * 0.6) return '#f59e0b'  // yellow — approaching
  return 'var(--text-secondary)'                               // normal
}
```

Display: `3 200 / 25 000 characters` with color-coded count. When over limit, show `⚠️ N over limit` and disable Save.

### Limits Info Block

Always show limits in the input modal so the user knows the constraints:

```
📏 Limits
• Maximum 25 000 characters per text (kuroshiro processing)
• Up to 20 custom texts can be saved
• Paragraphs over 500 chars will be split for translation
```

### Reader Integration

The Reader checks both library texts and custom texts:

```ts
const text = useMemo(() => {
  if (!id) return undefined
  const libText = texts.find((t) => t.id === id)
  if (libText) return libText
  const customText = customTexts.find((t) => t.id === id)
  if (customText) {
    const fullContent = sessionStorage.getItem(`custom-content-${id}`) || customText.content
    return { id: customText.id, title: customText.title, level: 'N5', tags: ['custom'], content: fullContent }
  }
  return undefined
}, [id, customTexts])
```

Show a purple `Custom` badge instead of the JLPT level badge for custom texts.

## Selection-Based Translation

Two translation UX patterns:

### 1. Paragraph Panel (🌐 toggle in toolbar)

Toggle button in the reader toolbar. When on, shows a panel below the text with each paragraph and a Translate button. Calls MyMemory per-paragraph:

```tsx
const [paraTranslations, setParaTranslations] = useState<Record<number, TranslationState>>({})

const handleParagraphTranslate = async (index: number, paraText: string) => {
  setParaTranslations(prev => ({ ...prev, [index]: { text: paraText, ru: '', en: '', loading: true } }))
  const result = await translateText(paraText, translationLang)
  setParaTranslations(prev => ({ ...prev, [index]: { text: paraText, ru: result.ru, en: result.en, loading: false } }))
}
```

### 2. Floating Translate Button (on text selection)

Listen for `mouseup`/`touchend` events. When selection contains Japanese characters, show a floating `🌐 Translate` button near the selection:

```tsx
useEffect(() => {
  const handler = () => {
    const sel = window.getSelection()
    const selectedText = sel?.toString().trim()
    if (selectedText && /[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]/.test(selectedText)) {
      const rect = sel!.getRangeAt(0).getBoundingClientRect()
      setSelectionPos({ x: rect.left + rect.width / 2 - 40, y: rect.top - 40 })
    } else {
      setSelectionPos(null)
    }
  }
  document.addEventListener('mouseup', handler)
  return () => document.removeEventListener('mouseup', handler)
}, [])
```

Both patterns use a shared `translateText()` utility with in-memory caching:

```ts
const cache = new Map<string, TranslationResult>()

export async function translateText(text: string, lang: TranslationLang): Promise<TranslationResult> {
  const cacheKey = `${text}|${lang}`
  if (cache.has(cacheKey)) return cache.get(cacheKey)!
  // ... fetch from MyMemory via Vite proxy ...
  cache.set(cacheKey, result)
  return result
}
```
