# Vite + kuromoji/kuroshiro Integration Pattern

## Overview

Integrating `kuroshiro` + `kuroshiro-analyzer-kuromoji` in a Vite React project requires solving three problems:
1. kuromoji is a CJS module incompatible with Vite's ESM pre-bundling
2. kuromoji uses Node.js APIs (`path.join`, `fs`) unavailable in browser
3. Dictionary `.dat.gz` files must be served as raw binary (not double-gzipped)

## Working vite.config.ts

```ts
import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Custom plugin to serve .dat.gz files as raw binary
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

export default defineConfig({
  plugins: [react(), kuromojiDictPlugin()],
  resolve: {
    alias: { 'path': 'path-browserify' }
  },
  define: {
    'process.env': '{}',
    'global': 'globalThis'
  },
  assetsInclude: ['**/*.dat', '**/*.dat.gz'],
  server: {
    proxy: {
      '/jisho': {  // or any external API
        target: 'https://jisho.org',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/jisho/, '')
      }
    }
  }
})
```

## Required npm packages

```bash
npm install kuroshiro kuroshiro-analyzer-kuromoji path-browserify
```

## Dictionary files

Kuromoji dictionary lives at `node_modules/kuromoji/dict/*.dat.gz`. Copy to `public/dict/`:

```json
// package.json scripts
"copy-dict": "mkdir -p public/dict && cp -r node_modules/kuromoji/dict/* public/dict/",
"predev": "npm run copy-dict",
```

## Type declarations

kuroshiro and kuromoji lack `@types/` packages. Create `src/types/kuroshiro.d.ts`:

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

## Singleton kuroshiro hook pattern

```ts
let instance: Kuroshiro | null = null
let initPromise: Promise<Kuroshiro> | null = null

function getKuroshiro(): Promise<Kuroshiro> {
  if (instance) return Promise.resolve(instance)
  if (initPromise) return initPromise
  initPromise = (async () => {
    const k = new Kuroshiro()
    await k.init(new KuromojiAnalyzer({ dictPath: '/dict' }))
    instance = k
    return k
  })()
  return initPromise
}
```

Key: the singleton lives at module level, NOT inside a React component. Multiple components share one instance. Show a loading spinner until `instanceRef.current` is set.

## Adding data-kanji attributes

kuroshiro outputs `<ruby>漢<rt>かん</rt>字<rt>じ</rt></ruby>` without data attributes. Post-process with regex:

```ts
result = result.replace(/<ruby>([^<]+)/g, '<ruby data-kanji="$1">$1')
```

Then use CSS `[data-kanji="X"] rt { visibility: hidden; }` for known-kanji hiding.

## MyMemory Translation API gotcha

Do NOT include the `de` parameter (email) — it returns "INVALID EMAIL PROVIDED" even with valid emails:

```
❌ /translate/get?q=text&langpair=ja|ru&de=user@example.com
✅ /translate/get?q=text&langpair=ja|ru
```

## Pitfalls

- **Node.js version**: Vite 5 requires Node >= 18. Always source nvm: `export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && nvm use 20`
- **Double gzip**: Vite's dev server gzips responses. `.dat.gz` files are already compressed. The custom `kuromojiDictPlugin` middleware MUST serve them as `application/octet-stream` without content-encoding.
- **CJS-to-ESM**: kuromoji uses `require()` internally. The `optimizeDeps.exclude: ['kuromoji']` from some tutorials BREAKS things — Vite needs to pre-bundle it to handle CJS. Don't exclude it unless you also provide path/process/global polyfills.
- **React Strict Mode**: causes useEffect to fire twice. The singleton pattern with `initPromise` handles this correctly, but make sure FuriganaText only calls `convert()` after `ready` (not just `!loading`).
- **SessionStorage for custom texts**: Don't put large user-uploaded texts (25k chars) in Zustand persist — it goes to localStorage and bloats the settings JSON. Use separate `sessionStorage` keys for full content, keep only metadata in localStorage.
