#!/usr/bin/env python3
"""Build N5 Anki deck: just extract + generate, no live translation."""
import json, re, os, sys

PATTERNS_PATH = "/Users/dmitrypotekhin/.hermes/jp_rag_data/patterns.jsonl"
PLAN_PATH = "/Users/dmitrypotekhin/.hermes/jp_rag_data/study_plan.json"
USER_VOCAB = "/Users/dmitrypotekhin/.hermes/jp_rag_data/user_vocab.json"
OUTPUT_PATH = "/Users/dmitrypotekhin/Downloads/N5_vocab_days.apkg"

SKIP = {
    "は","が","を","に","で","へ","と","も","の","や","か","から",
    "まで","より","ね","よ","さ","わ","な","ぞ","ぜ",
    "です","ます","だ","だろう","でしょう","たい","ない","ぬ",
    "いる","います","ある","あります","する","します","くる","きます",
    "いく","いきます","おる","なる","なります","できる",
    "この","その","あの","どの","これ","それ","あれ","どれ",
    "ここ","そこ","あそこ","どこ","こちら","そちら","あちら","どちら",
    "こんにちは","こんばんは","おはよう","さようなら","すみません",
    "はい","いいえ","うん","ううん",
    "わたし","わたしたち","あなた","あなたたち","かれ","かのじょ","かれら",
    "ひと","もの","こと","とき","ところ","ほう","ため","わけ","はず",
    "いち","に","さん","し","ご","ろく","しち","はち","く","じゅう",
    "ひゃく","せん","まん","れい","ぜろ",
    "たち","さま","さん","ちゃん","くん","どの","かた","がた",
    "ですから","ですが","では","じゃ",
    "そして","それから","しかし","でも","だから",
    "それで","それに","ところで","さて","ただし","または",
    "あ","ああ","あっ","ええ","えっと","あの","うーん",
    "かも","けど","けれど","けれども","ので","のに",
    "くらい","ぐらい","だけ","しか","ばかり",
    "について","にとって","によって","として","に対して",
    "だから","ですから","なぜなら","ただし","もしくは","かつ",
    "第","円","年","月","日","時","分","秒",
}

def parse_reading(raw):
    raw = raw.strip()
    m = re.match(r"^([^()]+?)(?:\(([^)]*)\))?$", raw)
    return (m.group(1).strip(), (m.group(2) or "").strip()) if m else (raw, "")

def get_words_from_hiragana(hira_s):
    hira_s = re.sub(r'^\(\d+\)\s*', '', hira_s).strip()
    hira_s = re.sub(r'[^\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\w\s]', '', hira_s)
    result = []
    for w in re.split(r'[\s/]+', hira_s):
        w = w.strip()
        if len(w) < 2 or w in SKIP:
            continue
        if re.match(r'^[ァ-ヶー]+$', w) or re.match(r'^[0-9０-９]+$', w):
            continue
        result.append(w)
    return result

def get_kanji_from_jap(jap_s, hira_w):
    jap_s = re.sub(r'^\(\d+\)\s*', '', jap_s).strip()
    if hira_w in jap_s:
        return None
    ks = re.findall(r'[\u4e00-\u9fff]+', jap_s)
    return max(ks, key=len) if ks else None

# Load data
print("Loading...", flush=True)
with open(PATTERNS_PATH) as f:
    all_p = {p["id"]: p for p in [json.loads(line) for line in f if line.strip()]}

with open(PLAN_PATH) as f:
    plan = json.load(f)

user_tr = {}
try:
    with open(USER_VOCAB) as f:
        uv = json.load(f)
    for v in uv.get("words", []):
        h = v.get("hiragana", "").strip()
        t = v.get("translation", "").strip()
        if h and t:
            user_tr[h] = t
except:
    pass

# Extract per day
all_seen = set()
day_vocab = {}

for day in plan["days"]:
    dn = day["day"]
    pats = day["patterns"]
    if not pats:
        day_vocab[dn] = {"title": day["title"], "items": []}
        continue
    items = []
    for pid in pats:
        p = all_p.get(pid)
        if not p: continue
        for v in p.get("vocabulary", []):
            word = v.get("word","").strip()
            raw = v.get("reading","").strip()
            meaning = v.get("meaning","").strip()
            if not word or not raw: continue
            hira, roma = parse_reading(raw)
            key = (word, hira)
            if key not in all_seen:
                all_seen.add(key)
                items.append({"kanji": word, "hiragana": hira, "romaji": roma,
                              "meaning": meaning, "src": [p.get("pattern_title", pid)]})
        jap_list = p.get("japanese_examples", [])
        hira_list = p.get("hiragana_examples", [])
        for i in range(min(len(jap_list), len(hira_list))):
            for w in get_words_from_hiragana(hira_list[i]):
                kanji = get_kanji_from_jap(jap_list[i], w) or w
                key = (kanji, w)
                if key not in all_seen:
                    all_seen.add(key)
                    items.append({"kanji": kanji, "hiragana": w, "romaji": "",
                                  "meaning": "", "src": [p.get("pattern_title", pid)]})
    seen = set()
    uniq = []
    for item in items:
        k = (item["kanji"], item["hiragana"])
        if k not in seen:
            seen.add(k)
            uniq.append(item)
    day_vocab[dn] = {"title": day["title"], "items": uniq}

# Extra patterns
extra_items = []
plan_ids = {pid for d in plan["days"] for pid in d["patterns"]}
for pid in sorted({p["id"] for p in all_p.values() if p.get("jlpt_level")=="N5"} - plan_ids):
    p = all_p[pid]
    for v in p.get("vocabulary", []):
        word = v.get("word","").strip()
        raw = v.get("reading","").strip()
        meaning = v.get("meaning","").strip()
        if not word or not raw: continue
        hira, roma = parse_reading(raw)
        key = (word, hira)
        if key not in all_seen:
            all_seen.add(key)
            extra_items.append({"kanji": word, "hiragana": hira, "romaji": roma,
                                "meaning": meaning, "src": [p.get("pattern_title", pid)]})
    jap_list = p.get("japanese_examples", [])
    hira_list = p.get("hiragana_examples", [])
    for i in range(min(len(jap_list), len(hira_list))):
        for w in get_words_from_hiragana(hira_list[i]):
            kanji = get_kanji_from_jap(jap_list[i], w) or w
            key = (kanji, w)
            if key not in all_seen:
                all_seen.add(key)
                extra_items.append({"kanji": kanji, "hiragana": w, "romaji": "",
                                    "meaning": "", "src": [p.get("pattern_title", pid)]})

seen2 = set()
extra_uniq = []
for item in extra_items:
    k = (item["kanji"], item["hiragana"])
    if k not in seen2:
        seen2.add(k)
        extra_uniq.append(item)

# Apply user translations
for dn, dv in day_vocab.items():
    for item in dv["items"]:
        if not item["meaning"]:
            item["meaning"] = user_tr.get(item["hiragana"], user_tr.get(item["kanji"], ""))
for item in extra_uniq:
    if not item["meaning"]:
        item["meaning"] = user_tr.get(item["hiragana"], user_tr.get(item["kanji"], ""))

# Stats
total = 0
translated = 0
print("\n=== STATS ===", flush=True)
for dn in sorted(day_vocab):
    dv = day_vocab[dn]
    cnt = len(dv["items"])
    total += cnt
    wm = sum(1 for i in dv["items"] if i["meaning"])
    translated += wm
    if cnt > 0:
        print(f"  Day {dn:2d} — {dv['title'][:30]:<30s} {cnt:3d} words ({wm:3d} translated)", flush=True)

print(f"  Extra{' ':<30s} {len(extra_uniq):3d} words", flush=True)
total += len(extra_uniq)
translated += sum(1 for i in extra_uniq if i["meaning"])
print(f"  TOTAL: {total} words ({translated} with translation)", flush=True)
print(f"  Untranslated: {total - translated} (Anki has built-in dictionary)", flush=True)

# Build Anki deck
print("\nBuilding Anki deck...", flush=True)
import genanki

model = genanki.Model(
    1657293845, "N5 по дням",
    fields=[{"name": "Kanji"}, {"name": "Hiragana"}, {"name": "Romaji"},
            {"name": "Meaning"}, {"name": "Source"}],
    templates=[
        {"name": "Kanji → Reading",
         "qfmt": "{{Kanji}}",
         "afmt": "{{FrontSide}}<hr id=answer><b>{{Hiragana}}</b><br>{{Romaji}}<br><br><i>{{Meaning}}</i><br><br><small style='color:#888;'>{{Source}}</small>"},
        {"name": "Hiragana → Kanji",
         "qfmt": "{{Hiragana}}",
         "afmt": "{{FrontSide}}<hr id=answer><b>{{Kanji}}</b><br><br><i>{{Meaning}}</i><br><br><small style='color:#888;'>{{Source}}</small>"},
        {"name": "Meaning → Kanji",
         "qfmt": "{{Meaning}}",
         "afmt": "{{FrontSide}}<hr id=answer><b>{{Kanji}}</b><br>{{Hiragana}} ({{Romaji}})<br><br><small style='color:#888;'>{{Source}}</small>"},
    ],
    css=(".card{font-family:'Hiragino Kaku Gothic Pro','Noto Sans JP',sans-serif;font-size:26px;text-align:center;padding:20px}"),
)

all_decks = []
BASE = "日本語 N5 :: По дням"

for dn in sorted(day_vocab):
    dv = day_vocab[dn]
    if not dv["items"]:
        continue
    deck = genanki.Deck(2058370300 + dn, f"{BASE}::День {dn} - {dv['title'][:40]}")
    for item in dv["items"]:
        s = "; ".join(item["src"][:3])
        if len(item["src"]) > 3:
            s += f" (+{len(item['src'])-3})"
        k = item["kanji"] if item["kanji"] != item["hiragana"] else item["hiragana"]
        m = item["meaning"] if item["meaning"] else ""
        note = genanki.Note(model=model, fields=[k, item["hiragana"], item["romaji"], m, s])
        deck.add_note(note)
    all_decks.append(deck)

if extra_uniq:
    deck = genanki.Deck(2058370399, f"{BASE}::Дополнительные")
    for item in extra_uniq:
        s = "; ".join(item["src"][:3])
        if len(item["src"]) > 3:
            s += f" (+{len(item['src'])-3})"
        k = item["kanji"] if item["kanji"] != item["hiragana"] else item["hiragana"]
        m = item["meaning"] if item["meaning"] else ""
        note = genanki.Note(model=model, fields=[k, item["hiragana"], item["romaji"], m, s])
        deck.add_note(note)
    all_decks.append(deck)

genanki.Package(all_decks).write_to_file(OUTPUT_PATH)
tn = sum(len(d.notes) for d in all_decks)
print(f"\nDONE! Saved to: {OUTPUT_PATH}", flush=True)
print(f"Notes: {tn}, Cards: {tn * 3}", flush=True)
