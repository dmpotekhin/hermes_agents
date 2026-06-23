#!/usr/bin/env python3
"""
Daily JLPT N5 lesson generator.
Determines current day of the study plan and generates a lesson message.
"""

import json
import os
import sys
from datetime import datetime, date

BASE_DIR = '/Users/dmitrypotekhin/Downloads/jp_rag_data'
PLAN_PATH = os.path.join(BASE_DIR, 'study_plan.json')
DATA_PATH = os.path.join(BASE_DIR, 'patterns.jsonl')
STATE_FILE = os.path.join(BASE_DIR, 'study_progress.json')

def load_patterns():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return {p['id']: p for p in (json.loads(line) for line in f) if p['jlpt_level'] == 'N5'}

def load_plan():
    with open(PLAN_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_current_day(start_date_str):
    """Calculate which day of the plan we're on."""
    start = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    today = date.today()
    delta = (today - start).days
    return delta + 1  # day 1 = start_date

def load_progress():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'completed_days': []}

def save_progress(progress):
    with open(STATE_FILE, 'w') as f:
        json.dump(progress, f)

def generate_lesson():
    patterns_dict = load_patterns()
    plan = load_plan()
    current_day = get_current_day(plan['start_date'])
    progress = load_progress()

    # Find the day in the plan
    day_data = None
    for d in plan['days']:
        if d['day'] == current_day:
            day_data = d
            break

    if not day_data:
        # Plan is over
        if current_day > plan['days'][-1]['day']:
            return f"🎉 План завершён! Ты прошёл все {len(plan['days'])} дней N5!"
        return f"⏳ День {current_day} не найден в плане."

    day_num = day_data['day']
    total_days = len(plan['days'])
    title = day_data['title']
    pattern_ids = day_data['patterns']
    topic = day_data['topic']

    lines = []
    lines.append(f"🇯🇵 *JLPT N5 — День {day_num}/{total_days}*")
    lines.append(f"📌 *{title}*")
    lines.append(f"⏱ Время: ~30-60 минут")
    lines.append("")

    # Progress bar
    pct = (day_num - 1) / total_days * 100
    filled = int(pct / 5)
    bar = '█' * filled + '░' * (20 - filled)
    lines.append(f"Прогресс: {bar} {pct:.0f}%")
    lines.append("")

    if topic == 'review':
        # Review day - no new patterns
        lines.append("📝 *Повторение пройденного*")
        lines.append("")
        lines.append("1. Прочитай вслух примеры из прошлых уроков")
        lines.append("2. Закрой японский текст — переведи с русского обратно")
        lines.append("3. Напиши 3 своих предложения с каждым паттерном")
        lines.append("")
        # Get patterns from last 4 days
        prev_days = [d for d in plan['days'] if d['day'] < day_num and d['day'] >= day_num - 4 and d['patterns']]
        seen_ids = set()
        for pd in prev_days:
            for pid in pd['patterns']:
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                pat = patterns_dict.get(pid)
                if pat:
                    lines.append(f"• {pat['pattern_title'][:50]}")
        lines.append("")
        lines.append("💡 *Совет:* читай вслух 5-7 раз каждый пример!")
        return '\n'.join(lines)

    if topic == 'final':
        lines.append("🎯 *Финальный тест!*")
        lines.append("")
        lines.append("Проверь себя:")
        lines.append("")
        # Random pick of 10 patterns
        all_ids = []
        for d in plan['days']:
            all_ids.extend(d['patterns'])
        import random
        random.seed(42)
        test_ids = random.sample(all_ids, min(10, len(all_ids)))
        for i, pid in enumerate(test_ids, 1):
            pat = patterns_dict.get(pid)
            if pat:
                lines.append(f"{i}. Объясни паттерн: {pat['pattern_title'][:45]}")
        lines.append("")
        lines.append("💡 Напиши мне в Telegram — я проверю!")
        return '\n'.join(lines)

    # Regular lesson day
    for pid in pattern_ids:
        pat = patterns_dict.get(pid)
        if not pat:
            continue

        title_jp = pat['pattern_title']
        meaning = pat['meaning'][:120] if pat['meaning'] else ''
        formation = pat['formation'][:100] if pat['formation'] else ''

        lines.append(f"━━━ {title_jp} ━━━")

        if formation:
            lines.append(f"🔧 *Формула:* {formation}")

        if meaning:
            lines.append(f"📖 *Объяснение:* {meaning}")

        # Show first 2 Japanese examples with translation
        if pat['japanese_examples']:
            lines.append(f"")
            lines.append("🇯🇵 *Примеры:*")
            for i, ex in enumerate(pat['japanese_examples'][:2]):
                en = pat['english_examples'][i] if i < len(pat['english_examples']) else ''
                hira = pat['hiragana_examples'][i] if i < len(pat['hiragana_examples']) else ''
                lines.append(f"  `{ex}`")
                if hira:
                    lines.append(f"   *Чтение:* {hira}")
                if en:
                    lines.append(f"   *Перевод:* {en}")
                lines.append("")

        # Show vocabulary
        if pat['vocabulary']:
            lines.append(f"📝 *Новые слова:*")
            for v in pat['vocabulary'][:4]:
                lines.append(f"  {v['word']} ({v['reading']}) — {v['meaning']}")
            lines.append("")

    # Practice section
    lines.append("━━━ *Практика* ━━━")
    lines.append("")
    lines.append("1️⃣ Прочитай вслух каждый пример 5-7 раз")
    lines.append("2️⃣ Закрой японский — переведи с русского")
    lines.append("3️⃣ Составь своё предложение по формуле")
    lines.append("4️⃣ Запиши его в тетрадь")
    lines.append("")
    lines.append("✍️ Напиши мне в Telegram свои примеры — я проверю!")

    return '\n'.join(lines)


if __name__ == '__main__':
    lesson = generate_lesson()
    print(lesson)
