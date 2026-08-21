# Japanese Reader — Project Reference

Concrete app built with this skill. Path: `/Users/dmitrypotekhin/projects/japanese-reader`.

## Stack
- React 18 + Vite 5.4 + Tailwind 3.4 + TypeScript 5.3
- kuroshiro + kuroshiro-analyzer-kuromoji (furigana), react-router-dom, zustand (settings store)
- dict files copied to `public/dict` via `predev` → `copy-dict` script

## Run
System Node is **v14** (too old for Vite 5). Use nvm:
```bash
cd /Users/dmitrypotekhin/projects/japanese-reader
source ~/.nvm/nvm.sh && nvm use 20
npm run dev   # predev auto-copies dict; dev server on :5173
```

## Structure
- `src/pages/` — Home (series grid + JLPT/tag filters + carousel), Reader (sidebar + reading area), Settings, Dashboard (reading stats), Flashcards (flip-card review)
- `src/components/` — AudioPlayer, CustomTextModal, FuriganaText, FuriganaToggle, TextCard, WordPopup
- `src/hooks/` — useKuroshiro (singleton), useSpeech, useCustomTexts
- `src/store/settingsStore.ts` — zustand (theme, animeTheme, fontSize, furigana, translationLang, read tracking)
- `src/data/texts.ts` + `texts.json` — 125 texts (25 topics × 5 JLPT levels)
- `src/utils/translate.ts` — MyMemory translation with in-memory cache
- `design/satori-reader-inspired.html` — earlier static design prototype
- `design/redesign-prototype.html` — approved redesign mockup (kanji covers, serif, warm paper)

## Design state (Satori Reader redesign, commit c01bd01 → 783f85f)
- "Satori Reader" aesthetic: grey cards, accent `#8BB8D6`, warm accent `#D4A574`.
- Anime background themes (CSS-only, no images): sakura / torii / waves / starry / clean,
  applied via `.bg-anime-*` classes on `#app-root`, cycled from a header button.
- Design tokens in `src/index.css` `:root` (`--sr-*`) + mirrored in `tailwind.config.js` (`colors.sr`).
- Reader layout: 260px sidebar (editions + display settings) + reading column (max 680px).
- Fonts: Roboto (body) + Noto Sans JP (UI) + Noto Serif JP (reading text), loaded from Google Fonts.
- Commit 783f85f (2026-08): series emoji → kanji covers (first kanji of title on a themed gradient),
  reading area `#FFFFFF` → warm paper `var(--sr-reading)` `#F7F4ED`, reading text → `font-serif-jp`
  (Noto Serif JP) with `.furigana-text rt` (Sans, 0.52em, `#8b8478`), deterministic "added" dates
  (index-based, no `Math.random()`), hover lift on cards.

## Known UI rough edges (reviewed 2026-08; visual items resolved in 783f85f)
Resolved:
- Series "cover" icons emoji → kanji cover art (themed gradient + first kanji of title). ✔
- Reading area hardcoded `#FFFFFF` → warm paper `var(--sr-reading)` `#F7F4ED`. ✔
- Japanese text Sans → `font-serif-jp` (Noto Serif JP). ✔
- Fake `Math.random()` dates → deterministic index-based dates. ✔ (still synthetic — no real `createdAt` in data)

Still open (functional, not visual):
- Sidebar no-ops: furigana "Known words"/"None", kanji "Known only", "Reveal on hover" checkbox
  (defaultChecked, not wired). "Group by difficulty" does nothing.
- Add a real `createdAt` field to `texts.json` if true dates are wanted (currently derived).

## Dashboard & Flashcards pages (commit d76d7b0, 2026-08)
The "Dashboard" and "Flashcards" nav buttons were dead `<span>` placeholders since the first
commit. Now real routes, active-nav highlighting, and functional pages.

**Data-model gotcha — `knownKanji` is WORDS, not kanji characters.** Despite the name,
`settingsStore.knownKanji: string[]` holds full words (e.g. `"公園"`), populated by WordPopup's
"I know this kanji ✓" button on the clicked word — NOT single chars. `readTexts: string[]` holds
text ids (set when a Reader mounts). Reuse these two arrays for any stats/review feature; don't
assume `knownKanji` is per-character.

- **Dashboard** (`/dashboard`): stat cards (texts read `X/125`, known words, custom texts,
  est. reading time `charsRead/250`), overall progress bar, JLPT-level breakdown. Computed from
  `texts` + `readTexts` + `knownKanji` + `useCustomTexts()`; no new backend/state needed.
- **Flashcards** (`/flashcards`): deck built from `knownKanji` → readings via
  `toHiragana()` / `toRomaji()` (kuroshiro) + meaning via jisho (`/jisho/api/v1/search/words?keyword=`).
  3D flip card (`.flashcard*` CSS in `src/index.css`), Shuffle / Prev / Next / Remove. Empty state
  when `knownKanji` is empty. Readings are pre-fetched in parallel on mount (deck is small).

## Reference sites for reading-UI inspiration
Satori Reader (satorireader.com), LingQ (lingq.com), japanese.io, NHK News Web Easy
(www3.nhk.or.jp/news/easy), JPDB (jpdb.io), Bunpro (bunpro.jp).
