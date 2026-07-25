#!/usr/bin/env python3
"""Update Perplexity_N5_30days_v2.md with 3-5 new words per day from the N5 batch"""
import json, re, os

PERPLEXITY_PLAN = "/Users/dmitrypotekhin/.hermes/jp_rag_data/Perplexity_N5_30days_v2.md"
NEW_WORDS = "/tmp/n5_new_words_v2.json"

with open(NEW_WORDS) as f:
    new_words = json.load(f)

# Index new words by theme
by_theme = {}
for w in new_words:
    t = w['theme']
    if t not in by_theme:
        by_theme[t] = []
    by_theme[t].append(w)

print("New words available by theme:")
for t, words in sorted(by_theme.items()):
    print(f"  {t}: {len(words)} words")

# Day 1: Знакомство → знакомство theme
# Day 2: Вопросы → вопросы
# Day 3: あります/います → дом/места
# Day 4: прилагательные → прилагательные
# Day 5: REVIEW - skip
# Day 6: прошедшее → глаголы
# Day 7: ています → глаголы
# Day 8: отрицание → глаголы
# Day 9: REVIEW - skip
# Day 10: счёт → числа
# Day 11: просьбы → глаголы (て-form)
# Day 12: хочу → глаголы
# Day 13: можно/нельзя → глаголы
# Day 14: REVIEW - skip
# Day 15: время → время
# Day 16: причина → mostly grammar
# Day 17: последовательность → mostly grammar
# Day 18: сравнения → прилагательные
# Day 19: предложения → глаголы
# Day 20: REVIEW - skip
# Day 21: еда → еда
# Day 22: погода → природа
# Day 23: дорога → места/вещи
# Day 24: хобби → хобби/глаголы
# Day 25: REVIEW - skip
# Day 26: покупки → вещи/числа
# Day 27: телефон → вещи/работа
# Day 28: REVIEW - skip
# Day 29: путешествие → места/вещи
# Day 30: финальный тест - skip

day_updates = {
    1:  ['время', ['今年','来年','毎日','今日']],
    2:  ['вопросы', ['どう','なぜ','どの','どんな','いくら']],
    3:  ['дом', ['机','椅子','本棚','ベッド','棚']],
    4:  ['прилагательные', ['新しい','古い','安い','広い','楽しい','小さい']],
    6:  ['глаголы', ['起きました','歩きました','勉強しました','話しました','待ちました']],
    7:  ['глаголы', ['起きる','勉強する','歩く','走る','泳ぐ']],
    8:  ['глаголы', ['見ません','話しません','書きません','勉強しません']],
    10: ['числа', ['百','千','一つ','二つ','三つ']],
    11: ['глаголы', ['来る','読む','書く','使う','入る']],
    12: ['глаголы', ['会う','買う','読む','聞く','食べる']],
    13: ['глаголы', ['入る','使う','帰る','座る','撮る']],
    15: ['время', ['半','毎朝','午前','午後','夕方','週間']],
    16: ['дом', ['用事','予定','都合','時間']],
    17: ['время', ['毎朝','毎晩','朝','夜','後']],
    18: ['прилагательные', ['大きい','長い','短い','高い','安い','新しい']],
    19: ['глаголы', ['買い物','散歩','休み','旅行','映画']],
    21: ['еда', ['肉','魚','野菜','果物','スープ','サラダ','料理']],
    22: ['природа', ['曇り','晴れ','風','雪','暖かい','涼しい']],
    23: ['места', ['バス','タクシー','電車','地下鉄','交差点','道']],
    24: ['наречия', ['よく','時々','毎日','いつも','あまり']],
    26: ['вещи', ['靴','帽子','色','安い','新しい','店']],
    27: ['вещи', ['電話','番号','メッセージ','後で','すぐ']],
    29: ['места', ['駅','タクシー','バス','遠い','近い']],
}

# Read the plan file
with open(PERPLEXITY_PLAN, encoding='utf-8') as f:
    content = f.read()

# For each day, find the vocabulary section and add words
for day_num, (theme, word_batch) in day_updates.items():
    # Find words from the batch that are actually available
    available = by_theme.get(theme, [])
    
    # Find each word in available list
    found_words = []
    for target in word_batch:
        for w in available:
            if w['kanji'] == target or w['hiragana'] == target or target in w['kanji']:
                found_words.append(w)
                break
    
    # If not found in theme, search all words
    if len(found_words) < 3:
        for target in word_batch:
            if not any(f['kanji'] == target or f['hiragana'] == target for f in found_words):
                for w in new_words:
                    if w['kanji'] == target or w['hiragana'] == target or target in w['kanji']:
                        found_words.append(w)
                        break
    
    if not found_words:
        print(f"Day {day_num}: NO WORDS FOUND for {word_batch}")
        continue
    
    # Create the addition text
    addition = "\n**Новые слова (из N5-списка):**\n"
    addition += f"| Кандзи | Хирагана | Ромадзи | Перевод |\n"
    addition += f"|--------|----------|---------|---------|\n"
    for w in found_words[:5]:
        r = w['romaji'] if w['romaji'] else '—'
        addition += f"| {w['kanji']} | {w['hiragana']} | {r} | {w['translation']} |\n"
    addition += "\n"
    
    # Find where to insert - look for Сценарий: line in that day
    # Each day section starts with ### День N
    day_header = f"### День {day_num}"
    day_idx = content.find(day_header)
    
    if day_idx == -1:
        print(f"Day {day_num}: section not found!")
        continue
    
    # Find the scenario line (Сценарий) for this day
    next_day_header = content.find(f"### День {day_num+1}")
    if next_day_header == -1:
        # Maybe next is --- or end of file
        next_day_header = content.find("## 📌 Как пользоваться")
    if next_day_header == -1:
        next_day_header = len(content)
    
    day_section = content[day_idx:next_day_header]
    
    # Find Сценарий line to insert before it
    scenario_idx = day_section.find("**Сценарий")
    if scenario_idx == -1:
        # Try Промпт line
        scenario_idx = day_section.find("**Промпт")
    if scenario_idx == -1:
        # Try --- footer
        scenario_idx = day_section.rfind("\n---")
        if scenario_idx == -1:
            scenario_idx = len(day_section)
    
    insert_pos = day_idx + scenario_idx
    
    # Place new vocabulary block BEFORE scenario/prompt
    content = content[:insert_pos] + addition + content[insert_pos:]
    
    print(f"Day {day_num} ({theme}): added {len(found_words[:5])} words - {', '.join(w['kanji'] for w in found_words[:5])}")

# Write updated file
with open(PERPLEXITY_PLAN, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Perplexity plan updated!")
print(f"Updated {len(day_updates)} days")
