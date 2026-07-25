---
name: japanese-nlp-browser
description: "Japanese text processing in browser apps (React/Vite) — kuroshiro, kuromoji, furigana, dictionary APIs, translation APIs. Use when adding Japanese NLP features to any frontend project."
version: 1.0.0
author: agent
created_by: agent
metadata:
  tags: [japanese, nlp, browser, vite, kuroshiro, kuromoji, furigana]
---

# Japanese NLP in Browser (React/Vite)

Integrate Japanese text processing into browser-based apps: furigana (ruby) annotations, morphological analysis, dictionary lookup, and machine translation.

## Quick Start

```bash
npm install kuroshiro kuroshiro-analyzer-kuromoji path-browserify
```

```ts
// vite.config.ts — essential additions
export default defineConfig({
  resolve: {
    alias: { 'path': 'path-browserify' }       // kuromoji uses path.join
  },
  define: {
    'process.env': '{}',                        // kuromoji checks process.env
    'global': 'globalThis'                      // kuromoji references global
  },
  assetsInclude: ['**/*.dat', '**/*.dat.gz'],   // dict files as static assets
  optimizeDeps: { include: ['kuromoji'] },      // pre-bundle CJS module
  // ... custom plugin for dict serving (see below)
})
```

## Core Patterns

### 1. Kuromoji Dictionary Serving

Kuromoji loads `.dat.gz` dictionary files at runtime via XHR. Vite's dev server applies gzip content-encoding to responses — this DOUBLE-COMPRESSES the already-gzipped dictionary files, causing "invalid file signature" errors at runtime.

**Fix:** custom Vite plugin that intercepts `.dat.gz` requests and serves them as raw binary (`application/octet-stream`) without content-encoding:

```ts
// Inside vite.config.ts
function kuromojiDictPlugin(): Plugin {
  return {
    name: 'kuromoji-dict',
    configureServer(server) {
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
```

**Dict file copy script** (package.json):
```json
{
  "scripts": {
    "copy-dict": "mkdir -p public/dict && cp -r node_modules/kuromoji/dict/* public/dict/",
    "predev": "npm run copy-dict"
  }
}
```

### 2. Kuroshiro Singleton Hook

Kuroshiro + KuromojiAnalyzer initialization is slow (1-3s for dictionary loading). Use a module-level singleton pattern so it initializes once across the entire app:

```ts
import Kuroshiro from 'kuroshiro'
import KuromojiAnalyzer from 'kuroshiro-analyzer-kuromoji'

let kuroshiroInstance: Kuroshiro | null = null
let initPromise: Promise<Kuroshiro> | null = null

function getKuroshiro(): Promise<Kuroshiro> {
  if (kuroshiroInstance) return Promise.resolve(kuroshiroInstance)
  if (initPromise) return initPromise

  initPromise = (async () => {
    const kuroshiro = new Kuroshiro()
    await kuroshiro.init(new KuromojiAnalyzer({ dictPath: '/dict' }))
    kuroshiroInstance = kuroshiro
    return kuroshiro
  })()

  return initPromise
}

export function useKuroshiro() {
  const [loading, setLoading] = useState(true)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const instanceRef = useRef<Kuroshiro | null>(null)

  useEffect(() => {
    let cancelled = false
    getKuroshiro()
      .then((k) => { if (!cancelled) { instanceRef.current = k; setLoading(false); setReady(true) } })
      .catch((err) => { if (!cancelled) { setError(err.message); setLoading(false) } })
    return () => { cancelled = true }
  }, [])

  const convert = useCallback(async (text: string) => {
    const k = instanceRef.current
    if (!k) throw new Error('Kuroshiro not initialized')
    return await k.convert(text, { mode: 'furigana', to: 'hiragana' })
  }, [])

  return { convert, loading, ready, error }
}
```

**Pitfall:** React StrictMode double-invokes effects. Always use a `ready` flag (separate from `loading`) and only call `convert()` when ready is true. Calling convert before kuroshiro is initialized throws "Kuroshiro not initialized".

### 3. Adding data-kanji Attributes

Kuroshiro outputs `<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>` — no `data-kanji` attributes. For CSS-based per-kanji furigana control, post-process the HTML:

```ts
let result = await kuroshiro.convert(text, { mode: 'furigana', to: 'hiragana' })

// Add data-kanji to each <ruby> tag
result = result.replace(
  /<ruby>([^<]+)/g,
  '<ruby data-kanji="$1">$1'
)
```

This enables CSS targeting like:
```css
.known-kanji-mode [data-kanji="公園"] rt { visibility: hidden; }
```

### 4. TypeScript Declarations

Both kuroshiro and kuroshiro-analyzer-kuromoji lack `@types` packages. Add a declaration file:

```ts
// src/types/kuroshiro.d.ts
declare module 'kuroshiro' { /* ... */ }
declare module 'kuroshiro-analyzer-kuromoji' { /* ... */ }
```

### 5. Furigana Toggle — CSS Only (No Re-render)

- Convert text with kuroshiro ONCE, store the HTML
- Global toggle: add/remove `.hide-furigana` class on container
- Per-kanji toggle: generate `<style>` block with per-kanji `rt { visibility: hidden }` rules
- CSS class: `.hide-furigana rt { visibility: hidden; }`

Never re-run kuroshiro conversion on toggle — it's expensive.

## Dictionary & Translation APIs

### jisho.org (Free, No Key)

Japanese word dictionary. Must be proxied through Vite to avoid CORS:

```ts
// vite.config.ts proxy
'/jisho': {
  target: 'https://jisho.org',
  changeOrigin: true,
  rewrite: (p) => p.replace(/^\/jisho/, '')
}
```

Fetch pattern:
```ts
const res = await fetch(`/jisho/api/v1/search/words?keyword=${encodeURIComponent(word)}`)
const json = await res.json()
const entry = json.data?.[0]
const reading = entry.japanese?.[0]?.reading
const definitions = entry.senses?.[0]?.english_definitions
```

### MyMemory (Free Translation, No Key)

Machine translation API. Japanese → Russian/English. Proxy through Vite:

```ts
// vite.config.ts proxy
'/translate': {
  target: 'https://api.mymemory.translated.net',
  changeOrigin: true,
  rewrite: (p) => p.replace(/^\/translate/, '')
}
```

**Pitfall:** do NOT include the `de` (email) parameter in the query string. The free tier works without it. Including a fake email returns: `"INVALID EMAIL PROVIDED"`. Correct URL:

```
/translate/get?q=${encodeURIComponent(text)}&langpair=ja|${targetLang}
```

Cache translations in-memory (`Map<string, {ru, en}>`) to avoid repeated API calls for the same text. Free tier limit: ~1000 requests/day.

**Two UX patterns for translation (see `japanese-text-processing` skill for code):**
- **Paragraph panel** — 🌐 toggle in reader toolbar shows per-paragraph Translate buttons
- **Floating translate** — select text → floating 🌐 button appears near selection

## Voice

### Web Speech API (Browser TTS)

```ts
const utterance = new SpeechSynthesisUtterance(text)
utterance.lang = 'ja-JP'
utterance.rate = 0.8
window.speechSynthesis.speak(utterance)
```

**Pitfall:** `onboundary` events for word highlighting are unreliable for Japanese — depends on browser/OS TTS engine. Always wrap in try/catch; silently skip highlighting if events don't fire.

For per-word pronunciation (one word at a time), create a fresh `SpeechSynthesisUtterance` instance each time.

## Node.js Version

Kuromoji and Vite 5 require **Node.js >= 18**. If the system has an older Node, use nvm:

```bash
nvm use 20
```

## References

- `references/kuromoji-vite-integration.md` — full vite.config.ts with all plugins and middleware, plus explanation of why each piece is needed
- `references/api-endpoints.md` — jisho.org, MyMemory, and KanjiVG API response shapes and pitfalls
