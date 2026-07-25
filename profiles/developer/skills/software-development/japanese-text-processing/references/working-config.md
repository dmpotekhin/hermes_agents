# Working vite.config.ts from japanese-reader project

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

# Working package.json scripts

```json
{
  "scripts": {
    "copy-dict": "mkdir -p public/dict && cp -r node_modules/kuromoji/dict/* public/dict/",
    "predev": "npm run copy-dict",
    "dev": "vite",
    "build": "tsc && npm run copy-dict && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "kuroshiro": "^1.2.0",
    "kuroshiro-analyzer-kuromoji": "^1.1.0",
    "path-browserify": "^1.0.1",
    "react": "^18.3.1",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.30.4",
    "zustand": "^4.5.7"
  },
  "devDependencies": {
    "@types/react": "^18.3.31",
    "@types/react-dom": "^18.3.7",
    "@vitejs/plugin-react": "^4.7.0",
    "autoprefixer": "^10.5.4",
    "postcss": "^8.5.21",
    "tailwindcss": "^3.4.19",
    "typescript": "5.3",
    "vite": "^5.4.21"
  }
}
```
