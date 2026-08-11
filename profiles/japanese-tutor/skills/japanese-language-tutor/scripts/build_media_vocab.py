#!/usr/bin/env python3
"""
build_media_vocab.py — Шаблон для построения словаря из SRT-субтитров
=====================================================================
Техника «курированный словарь + частотная верификация».

Как использовать:
1. Скопировать этот файл в ~/.hermes/jp_rag_data/build_<media>_vocab.py
2. Настроить MEDIA_DIR на папку с SRT-файлами
3. Заполнить CURATED_VOCAB — вручную отобранные слова с переводами
4. Запустить: python3 build_<media>_vocab.py

Результат:
- <media>_vocab.json — основной словарь
- <media>_phrasebook.md — текстовый справочник для пользователя
- <media>_extra_words.json — неизвестные катакана-слова

Основано на: Pokemon (283 SRT, 207 слов, 201 найдено в субтитрах)
"""

import os
import re
import json
import unicodedata
from collections import Counter, defaultdict

# ═══════════════════════════════════════════════
# НАСТРОЙКИ — ИЗМЕНИТЬ ПОД СВОЙ ПРОЕКТ
# ═══════════════════════════════════════════════

MEDIA_DIR = "/Users/dmitrypotekhin/Downloads/ПУТЬ/К/SRT/"
OUTPUT_DIR = "/Users/dmitrypotekhin/.hermes/jp_rag_data"
MEDIA_NAME = "media"  # будет использовано в именах файлов

# ═══════════════════════════════════════════════
# CORE-СЛОВАРЬ — ЗАПОЛНИТЬ ВРУЧНУЮ
# Формат: (kanji_or_word, hiragana, translation, category)
# ═══════════════════════════════════════════════

CURATED_VOCAB = [
    # === Имена персонажей ===
    ("ГЕРОЙ", "ГЕРОЙ", "Имя героя", "имена"),
    
    # === Мир сериала ===
    ("КЛЮЧЕВОЕ_СЛОВО", "ключевое_слово", "перевод", "мир"),
    
    # === Команды ===
    ("いけ", "いけ", "Вперёд!", "команды"),
    ("まて", "まて", "Стой!", "команды"),
    
    # === Эмоции ===
    ("すごい", "すごい", "Потрясающе!", "эмоции"),
    ("やった", "やった", "Ура!", "эмоции"),
    
    # === Фразы ===
    ("大丈夫", "だいじょうぶ", "Всё в порядке", "фразы"),
    ("なるほど", "なるほど", "Вот оно что", "фразы"),
]

# ═══════════════════════════════════════════════
# КОД — ОБЫЧНО НЕ ТРОГАТЬ
# ═══════════════════════════════════════════════

def is_kanji(ch):
    return 0x4E00 <= ord(ch) <= 0x9FFF

def is_jp_char(ch):
    return is_kanji(ch) or (0x3040 <= ord(ch) <= 0x309F) or (0x30A0 <= ord(ch) <= 0x30FF)

def extract_text_from_srt(filepath):
    texts = []
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except Exception:
        return texts
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.isdigit() or '-->' in line:
            continue
        if all(c in '♪～♫♬' for c in line):
            continue
        if re.match(r'^[（(][^）)]*[）)]$', line):
            continue
        if not any(is_jp_char(c) for c in line):
            continue
        text = unicodedata.normalize('NFKC', line)
        text = re.sub(r'[（(][^）)]*[）)]', '', text)
        text = text.strip()
        if len(re.findall(r'[\u3040-\u9fff\u30a0-\u30ff]+', text)) < 2:
            continue
        texts.append(text)
    return texts


def build_vocab():
    print(f"\n🔍 {MEDIA_NAME.upper()} — ПОСТРОЕНИЕ СЛОВАРЯ")
    
    # Шаг 1: Загрузить CORE
    print("\n📚 Шаг 1: Загрузка CORE-словаря...")
    curated = {}
    for kanji, hiragana, trans, cat in CURATED_VOCAB:
        curated[kanji] = {
            'kanji': kanji if any(is_kanji(c) for c in kanji) else '',
            'hiragana': hiragana,
            'translation': trans,
            'category': cat,
            'frequency': 0
        }
        if hiragana != kanji and hiragana not in curated:
            curated[hiragana] = curated[kanji]
    print(f"  Слов в CORE: {len(CURATED_VOCAB)}")
    
    # Шаг 2: Сканировать SRT
    print("\n📁 Шаг 2: Сканирование SRT...")
    srt_files = []
    for root, dirs, files in os.walk(MEDIA_DIR):
        for f in files:
            if f.endswith('.srt'):
                srt_files.append(os.path.join(root, f))
    srt_files.sort()
    print(f"  Найдено SRT: {len(srt_files)}")
    
    print("\n🔍 Шаг 3: Поиск слов в субтитрах...")
    all_texts = []
    for i, path in enumerate(srt_files):
        if i % 50 == 0:
            print(f"  {i}/{len(srt_files)}...")
        texts = extract_text_from_srt(path)
        all_texts.extend(texts)
        
        for text in texts:
            for kanji, hiragana, trans, cat in CURATED_VOCAB:
                count = text.count(kanji)
                if count > 0:
                    curated[kanji]['frequency'] += count
                if hiragana != kanji and len(hiragana) >= 3:
                    pattern = r'(?:^|[、。！？「」　 \t\n\.\!\?\'\"\(\)\[\]…・])' + re.escape(hiragana) + r'(?:$|[、。！？「」　 \t\n\.\!\?\'\"\(\)\[\]…・])'
                    if re.search(pattern, text):
                        curated[hiragana]['frequency'] += 1
    
    # Шаг 4: Формирование словаря
    print("\n📊 Шаг 4: Формирование словаря...")
    vocab_words = []
    seen = set()
    for kanji, hiragana, trans, cat in CURATED_VOCAB:
        key = f"{kanji}|{hiragana}"
        if key in seen:
            continue
        seen.add(key)
        info = curated.get(kanji) or {}
        freq = info.get('frequency', 0)
        vocab_words.append({
            'kanji': kanji if any(is_kanji(c) for c in kanji) else '',
            'hiragana': hiragana,
            'romaji': '',
            'translation': trans,
            'category': cat,
            'frequency': freq,
            'note': ''
        })
    vocab_words.sort(key=lambda w: -w['frequency'])
    
    # Шаг 5: Дополнительные слова (катакана 3+)
    print("\n🔎 Шаг 5: Дополнительные слова...")
    full_text = ' '.join(all_texts)
    extra = re.findall(r'[ァ-ヺー]{3,}', full_text)
    extra_freq = Counter(extra)
    known = {w['hiragana'] for w in vocab_words}
    new_words = [{'hiragana': w, 'frequency': c, 'translation': '', 'category': 'extra'}
                 for w, c in extra_freq.most_common(50) if w not in known]
    
    # Шаг 6: Сохранение
    vocab_file = os.path.join(OUTPUT_DIR, f"{MEDIA_NAME}_vocab.json")
    phrasebook = os.path.join(OUTPUT_DIR, f"{MEDIA_NAME}_phrasebook.md")
    extra_file = os.path.join(OUTPUT_DIR, f"{MEDIA_NAME}_extra_words.json")
    
    result = {
        'info': {
            'description': f'Словарь из {MEDIA_NAME} ({len(srt_files)} SRT)',
            'created': '2026-07-27',
            'total_words': len(vocab_words),
            'source_files': len(srt_files),
            'source_texts': len(all_texts),
            'categories': sorted(set(w['category'] for w in vocab_words if w['category'] != 'extra'))
        },
        'words': vocab_words
    }
    
    with open(vocab_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Phrasebook
    cats = defaultdict(list)
    for w in vocab_words:
        if w['category'] != 'extra':
            cats[w['category']].append(w)
    
    with open(phrasebook, 'w', encoding='utf-8') as f:
        f.write(f"# 🎬 {MEDIA_NAME.capitalize()} Phrasebook\n\n")
        for cat in sorted(cats.keys()):
            f.write(f"---\n\n## {cat}\n\n")
            f.write("| Кандзи | Хирагана | Перевод | В субтитрах |\n")
            f.write("|--------|----------|---------|-------------|\n")
            for w in cats[cat]:
                k = w['kanji'] if w['kanji'] else '—'
                m = f"✅ ×{w['frequency']}" if w['frequency'] > 0 else "❌"
                f.write(f"| {k} | {w['hiragana']} | {w['translation']} | {m} |\n")
    
    with open(extra_file, 'w', encoding='utf-8') as f:
        json.dump(new_words, f, ensure_ascii=False, indent=2)
    
    # Статистика
    found = sum(1 for w in vocab_words if w['frequency'] > 0)
    print(f"\n✅ ГОТОВО!")
    print(f"  Слов: {len(vocab_words)} (найдено в субтитрах: {found})")
    print(f"  Категорий: {len(cats)}")
    print(f"  Доп. слов: {len(new_words)}")
    print(f"  Файлы: {vocab_file}, {phrasebook}, {extra_file}")

if __name__ == '__main__':
    build_vocab()
