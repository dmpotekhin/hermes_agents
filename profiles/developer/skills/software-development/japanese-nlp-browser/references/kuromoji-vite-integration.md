# Full Vite Config for Kuromoji + Browser

This is the complete `vite.config.ts` that handles all kuromoji/Vite integration issues:

```ts
import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

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
    alias: {
      'path': 'path-browserify',
    }
  },
  define: {
    'process.env': '{}',
    'global': 'globalThis'
  },
  assetsInclude: ['**/*.dat', '**/*.dat.gz'],
  optimizeDeps: {
    include: ['kuromoji']
  },
  server: {
    proxy: {
      '/jisho': {
        target: 'https://jisho.org',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/jisho/, '')
      },
      '/translate': {
        target: 'https://api.mymemory.translated.net',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/translate/, '')
      }
    }
  }
})
```

## Why Each Piece Exists

### `resolve.alias: { 'path': 'path-browserify' }`
Kuromoji's NodeDictionaryLoader uses `path.join()`. In the browser, this module doesn't exist. `path-browserify` provides a browser-compatible polyfill.

### `define: { 'process.env': '{}', 'global': 'globalThis' }`
Kuromoji checks for `process.env` and `global` at the top level. These shims prevent ReferenceErrors.

### `assetsInclude: ['**/*.dat', '**/*.dat.gz']`
Without this, Vite treats `.dat` and `.dat.gz` as unknown file types and may refuse to serve them or serve them incorrectly.

### `optimizeDeps: { include: ['kuromoji'] }`
Kuromoji is a CJS module. Vite's pre-bundling (via esbuild) converts CJS to ESM. Including it in optimizeDeps forces pre-bundling at dev server start rather than on first request.

### `kuromojiDictPlugin`
**Critical.** Without this plugin, Vite's dev server applies gzip `content-encoding` to `.dat.gz` file responses. The browser auto-decompresses, and kuromoji's BrowserDictionaryLoader tries to decompress the already-decompressed data → "invalid file signature" errors for all 12 dictionary files. The plugin intercepts `.dat.gz` requests and serves them as raw binary with no content-encoding.

### Proxy setup
Both jisho.org and MyMemory API would hit CORS errors if called directly from the browser. Vite's dev server proxy strips the `/jisho` and `/translate` prefixes and forwards the request server-side.

## Dictionary File Layout

```
public/dict/
├── base.dat.gz
├── cc.dat.gz
├── check.dat.gz
├── tid.dat.gz
├── tid_map.dat.gz
├── tid_pos.dat.gz
├── unk.dat.gz
├── unk_char.dat.gz
├── unk_compat.dat.gz
├── unk_invoke.dat.gz
├── unk_map.dat.gz
└── unk_pos.dat.gz
```

These are copied from `node_modules/kuromoji/dict/` via the npm `predev` script.
