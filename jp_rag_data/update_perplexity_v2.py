#!/usr/bin/env python3
"""Second attempt - broader matching for Perplexity plan update"""
import json, re

PERPLEXITY_PLAN = "/Users/dmitrypotekhin/.hermes/jp_rag_data/Perplexity_N5_30days_v2.md"
NEW_WORDS = "/tmp/n5_new_words_v2.json"

with open(NEW_WORDS) as f:
    new_words = json.load(f)

# Build a searchable index
all_kanji = {}  # kanji -> word
all_hira = {}   # hiragana -> word  
for w in new_words:
    all_kanji[w['kanji']] = w
    h = w['hiragana'].replace(' ','')
    all_hira[h] = w

def find_words(targets, max_per_day=5):
    """Find words from the batch matching target kanji"""
    found = []
    for t in targets:
        w = all_kanji.get(t)
        if not w:
            w = all_hira.get(t)
        if w and w not in found:
            found.append(w)
            if len(found) >= max_per_day:
                break
    return found

def find_by_theme(theme, max_words=5):
    """Find words by theme"""
    found = [w for w in new_words if w['theme'] == theme]
    return found[:max_words]

def find_verbs(max_words=5):
    """Find verb-type words"""
    found = [w for w in new_words if w['theme'] == 'глаголы' and w['hiragana'].endswith('う')]
    return found[:max_words]

# Day-by-day: smarter word selection from what's actually available
updates = {
    1:  find_words(['学生','今年','毎日','来年','毎週']),
    2:  find_words(['なぜ','どうして','いくら','いくつ','どう']),
    3:  find_words(['猫','犬','池','椅子','机','棚']),
    4:  find_by_theme('прилагательные', 5),
    6:  find_words(['歩く','勉強','起きる','待つ','話す','言う']),
    7:  find_words(['歩く','走る','泳ぐ','起きる','勉強','洗う','話す','言う']),
    8:  find_words(['見る','話す','書く','言う','勉強']),
    10: find_words(['百','千','一つ','二つ','三つ','四つ','五つ','六つ','七つ','八つ','九つ','十']),
    11: find_words(['来る','読む','書く','使う','入る','待つ','言う','見せる']),
    12: find_words(['会う','買う','読む','聞く','食べる','見る','行く','飲む']),
    13: find_words(['入る','使う','帰る','座る','撮る','待つ']),
    15: find_words(['半','毎朝','午前','午後','夕方','週間','毎晩','今朝']),
    16: find_words(['時間','予定','都合','理由']),
    17: find_words(['朝','夜','後','毎朝','毎晩']),
    18: find_by_theme('прилагательные', 5),
    19: find_words(['買い物','散歩','休み','旅行','映画','一緒']),
    21: find_by_theme('еда', 5),
    22: find_by_theme('природа', 5),
    23: find_words(['タクシー','地下鉄','電車','交差点','道','大通り','角']),
    24: find_words(['時々','よく','毎日','旅行','写真','映画','音楽','一緒']),
    26: find_words(['色','靴','帽子','店','一つ','三つ']),
    27: find_words(['電話','番号','メッセージ','後','すぐ']),
    29: find_words(['タクシー','地下鉄','駅','道','近い','遠い','バス']),
}

with open(PERPLEXITY_PLAN, encoding='utf-8') as f:
    content = f.read()

for day_num, found_words in sorted(updates.items()):
    found_words = [w for w in found_words if w]  # remove None
    
    if not found_words:
        print(f"Day {day_num}: no words found, trying theme fallback...")
        # Fallback: show what themes match this day
        continue
    
    # Deduplicate by kanji
    seen = set()
    unique = []
    for w in found_words:
        if w['kanji'] not in seen:
            seen.add(w['kanji'])
            unique.append(w)
    
    if not unique:
        continue
    
    # Create addition text
    addition = "\n**➕ Новые слова из N5-списка:**\n"
    addition += "| Кандзи | Хирагана | Ромадзи | Перевод |\n|--------|----------|---------|---------|\n"
    for w in unique[:5]:
        r = w['romaji'] if w['romaji'] else '—'
        t = w['translation'][:30]
        addition += f"| {w['kanji']} | {w['hiragana']} | {r} | {t} |\n"
    addition += "\n"
    
    # Find insertion point
    day_header = f"### День {day_num}"
    day_idx = content.find(day_header)
    if day_idx == -1:
        print(f"Day {day_num}: section not found!")
        continue
    
    # Find the end of this day's section
    next_day = content.find(f"### День {day_num+1}")
    if next_day == -1:
        next_day = content.find("## 📌 Как пользоваться")
    if next_day == -1:
        next_day = len(content)
    
    day_section = content[day_idx:next_day]
    
    # Insert before **Сценарий** or before day footer (---)
    for marker in ["**Сценарий:", "**Сценарий**", "**Сценарий"]:
        pos = day_section.find(marker)
        if pos != -1:
            insert_pos = day_idx + pos
            content = content[:insert_pos] + addition + content[insert_pos:]
            break
    else:
        # Insert before --- at end of day
        footer_idx = day_section.rfind("\n---")
        if footer_idx != -1:
            insert_pos = day_idx + footer_idx
            content = content[:insert_pos] + addition + content[insert_pos:]
        else:
            print(f"Day {day_num}: could not find insertion point!")
            continue
    
    print(f"Day {day_num}: added {len(unique[:5])} — {', '.join(w['kanji'] for w in unique[:5])}")

with open(PERPLEXITY_PLAN, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Done! Updated Perplexity plan.")
