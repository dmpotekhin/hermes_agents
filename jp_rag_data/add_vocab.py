#!/usr/bin/env python3
"""Add new words to user_vocab.json"""
import json
from datetime import date

INPUT_FILE = "/Users/dmitrypotekhin/.hermes/jp_rag_data/user_vocab.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

existing_hiragana = {w["hiragana"] for w in data["words"]}
existing_kanji = {w.get("kanji", "") for w in data["words"]}

print(f"Before: {len(data['words'])} words, max id = {max(w['id'] for w in data['words'])}")

new_words = [
    ("飲みます", "のみます", "nomimasu", "пить", "глаголы"),
    ("水", "みず", "mizu", "вода", "еда"),
    ("お茶", "おちゃ", "ocha", "чай", "еда"),
    ("コーヒー", "こーひー", "koohii", "кофе", "еда"),
    ("いつも", "いつも", "itsumo", "всегда", "наречия"),
    ("毎日", "まいにち", "mainichi", "каждый день", "время"),
    ("昨日", "きのう", "kinou", "вчера", "время"),
    ("食堂", "しょくどう", "shokudou", "столовая", "еда"),
    ("どう", "どう", "dou", "как?", "вопросы"),
    ("いかが", "いかが", "ikaga", "как? (вежливая форма)", "вопросы"),
]

next_id = max(w["id"] for w in data["words"]) + 1
added = []

for kanji, hira, romaji, trans, theme in new_words:
    if hira in existing_hiragana:
        print(f"  DUP (hira): {kanji} ({hira}) — skip")
        continue
    if kanji and kanji in existing_kanji:
        print(f"  DUP (kanji): {kanji} — skip")
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

print(f"\nAdded: {len(added)} words")
for w in added:
    print(f"  + {w['kanji']} ({w['hiragana']}, {w['romaji']}) — {w['translation']} [{w['theme']}]")

data["info"]["total_words"] = len(data["words"])
data["info"]["last_updated"] = "2026-07-02"
data["info"]["themes"] = sorted({w["theme"] for w in data["words"]})

with open(INPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nAfter: {len(data['words'])} words")
print("JSON written successfully")
