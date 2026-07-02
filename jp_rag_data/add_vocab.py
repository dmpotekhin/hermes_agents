#!/usr/bin/env python3
"""Add new words from Dialog 13 & 14 to user_vocab.json"""
import json

INPUT_FILE = "/Users/dmitrypotekhin/.hermes/jp_rag_data/user_vocab.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

existing_kanji = {w["kanji"]: w["hiragana"] for w in data["words"]}
existing_hiragana = {w["hiragana"] for w in data["words"]}

print(f"Before: {len(data['words'])} words")

candidates = [
    # Drinks from Dialog 13 word list
    ("紅茶", "こうちゃ", "koucha", "чёрный чай", "еда"),
    ("牛乳", "ぎゅうにゅう", "gyuunyuu", "молоко", "еда"),
    ("コーラ", "こーら", "koora", "кола", "еда"),
    ("日本酒", "にほんしゅ", "nihonshu", "сакэ", "еда"),
    ("ビール", "びーる", "biiru", "пиво", "еда"),
    ("ワイン", "わいん", "wain", "вино", "еда"),
    # Grammar / verb forms from commentary
    ("飲みました", "のみました", "nomimashita", "пил (прош. вр.)", "глаголы"),
    ("食べました", "たべました", "tabemashita", "кушал (прош. вр.)", "глаголы"),
    ("食べませんでした", "たべませんでした", "tabemasen deshita", "не кушал (прош. отр.)", "глаголы"),
    # Dialog 14
    ("昼ご飯", "ひるごはん", "hirugohan", "обед", "еда"),
    ("ラーメン屋", "らーめんや", "raamenya", "раменная", "еда"),
    ("とても", "とても", "totemo", "очень", "наречия"),
    ("そして", "そして", "soshite", "и, а затем", "частицы"),
    ("美味しい", "おいしい", "oishii", "вкусный", "прилагательные"),
    # Places from Dialog 14 word list
    ("レストラン", "れすとらん", "resutoran", "ресторан", "еда"),
    ("カフェ", "かふぇ", "kafe", "кафе", "еда"),
    ("うどん屋", "うどんや", "udonya", "лапшичная (удон)", "еда"),
    ("そば屋", "そばや", "sobaya", "лапшичная (соба)", "еда"),
    ("寿司屋", "すしや", "sushiya", "суши-бар", "еда"),
    ("ピザ屋", "ぴざや", "pizaya", "пиццерия", "еда"),
]

next_id = max(w["id"] for w in data["words"]) + 1
added = []

for kanji, hira, romaji, trans, theme in candidates:
    if kanji in existing_kanji:
        print(f"  DUP (kanji): {kanji} ({hira}) — exists")
        continue
    if hira in existing_hiragana:
        print(f"  DUP (hira): {kanji} ({hira}) — exists")
        continue
    w = {
        "id": next_id,
        "kanji": kanji,
        "hiragana": hira,
        "romaji": romaji,
        "translation": trans,
        "theme": theme,
        "date_added": "2026-07-02"
    }
    data["words"].append(w)
    added.append(w)
    next_id += 1

print(f"\n✅ Added: {len(added)} words")
for w in added:
    print(f"  + {w['kanji']} ({w['hiragana']}, {w['romaji']}) — {w['translation']} [{w['theme']}]")

# Update info
data["info"]["total_words"] = len(data["words"])
data["info"]["last_updated"] = "2026-07-02"
data["info"]["themes"] = sorted({w["theme"] for w in data["words"]})

with open(INPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nAfter: {len(data['words'])} words")
print(f"Themes: {data['info']['themes']}")
