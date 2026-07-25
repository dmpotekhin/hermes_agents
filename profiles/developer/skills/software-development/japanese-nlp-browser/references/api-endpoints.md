# API Response Shapes

## jisho.org — Word Search

**Endpoint:** `GET /api/v1/search/words?keyword={word}`

**Response shape (abridged):**
```json
{
  "meta": { "status": 200 },
  "data": [
    {
      "slug": "公園",
      "japanese": [
        { "reading": "こうえん", "word": "公園" }
      ],
      "senses": [
        {
          "english_definitions": ["(public) park"],
          "parts_of_speech": ["Noun"],
          "tags": []
        }
      ]
    }
  ]
}
```

**Extraction:**
```ts
const entry = json.data?.[0]
const reading = entry?.japanese?.[0]?.reading
const definitions = entry?.senses?.[0]?.english_definitions?.slice(0, 5)
```

**Notes:**
- Free, no API key required
- Must proxy through Vite to avoid browser CORS (target: `https://jisho.org`)
- Rate limit: reasonable for individual word lookups
- Some rare/obscure words may return empty data array

## MyMemory — Machine Translation

**Endpoint:** `GET /get?q={text}&langpair=ja|{target}`

**Response shape:**
```json
{
  "responseData": {
    "translatedText": "Мой дом к западу от Токио.",
    "match": 1
  },
  "responseStatus": 200
}
```

**Supported language pairs (relevant):**
- `ja|ru` — Japanese → Russian
- `ja|en` — Japanese → English

**Pitfalls:**
- Do NOT include `de` (email) parameter — the free tier works without it. Including a fake email returns `"INVALID EMAIL PROVIDED"`.
- The `match` field indicates confidence (1 = perfect match in TM, lower = machine translation)
- No API key required
- Must proxy through Vite (target: `https://api.mymemory.translated.net`)
- Daily limit: ~1000 requests/day for anonymous usage
- Response is always a single string — no per-word breakdown

## KanjiVG — Stroke Order Data

**Endpoint:** `GET https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{codepoint}.svg`

**Codepoint format:** 5-digit lowercase hex Unicode codepoint (e.g., 漢 → `06f22`, 一 → `04e00`)

```ts
function charToCodepoint(ch: string): string {
  const cp = ch.codePointAt(0)!
  return cp.toString(16).toLowerCase().padStart(5, '0')
}
```

**Response:** SVG XML with individual stroke paths marked as `<path id="kvg:StrokePaths_Kanji-{codepoint}-s{num}">`.

**Notes:**
- Free, CC BY-SA 3.0 license
- Covers all Jōyō and Jinmeiyō kanji
- Direct fetch from raw.githubusercontent.com — no CORS issues
- No API key required
