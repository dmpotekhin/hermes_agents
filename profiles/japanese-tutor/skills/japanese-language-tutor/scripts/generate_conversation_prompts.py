#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate full self-contained prompts for every day in the 30-day conversation plan.

Usage:
    python3 generate_conversation_prompts.py [path_to_plan.md]

Defaults to ~/.hermes/jp_rag_data/Perplexity_N5_30days_v2.md

What it does:
- Locates every "### День N" section
- For regular days: extracts the 4-column dictionary table (Кандзи | Хирагана | Ромадзи | Перевод)
  under **Словарь:** and builds a full self-contained prompt (role + theme + vocab + rules + "Начни диалог")
- For review days (5,9,14,20,25,28) and test day (30): inserts a REVIEW_TEMPLATE
- Replaces stub prompts ("Скопируй структуру Дня 1") and existing prompts; inserts where missing
- Day 1 keeps its own prompt (skipped)

Rules embedded in every prompt:
  1. Speak polite です/ます
  2. FORMAT: every Japanese phrase written as hiragana (romaji) — Russian translation
     (user reads along while the AI speaks; requirement 2026-08-04)
  3. Use the day's vocabulary
  4. Short sentences 3-5 words
  5. Correct mistakes, explain in Russian
  6. Escalate difficulty if user answers correctly
  7. PRONUNCIATION: speak like a native, no foreign accent, in voice mode read Japanese
     text, do NOT read romaji literally (わたし = "вата-щи", not "уоташи")
  8. Start the dialogue

PITFALLS:
- Days with NON-standard dictionary tables are NOT parsed (day 6 past tense, day 8 negation,
  day 10 counters, day 29 final RPG). After running, check for leftover stubs:
      grep -n "слова из темы дня" <file>
  and fill those vocab sections manually (see the 2026-08-04 session for the exact wording).
- Always back up first: cp <file> /tmp/backup_prompts.md
- Verify completeness after running:
      grep -c "Промпт:" <file>   # expect 29-30 (Day 1 uses "**Промпт для Perplexity:**")
"""
import re, sys

PATH = "/Users/dmitrypotekhin/.hermes/jp_rag_data/Perplexity_N5_30days_v2.md"
if len(sys.argv) > 1:
    PATH = sys.argv[1]

with open(PATH, encoding="utf-8") as f:
    lines = f.readlines()

day_idxs = [i for i, l in enumerate(lines) if l.startswith("### День ")]
day_idxs.append(len(lines))

def get_theme(header):
    m = re.search(r"—\s*(.+)", header)
    return m.group(1).strip() if m else header.strip()

def find_dict_block(sec):
    """Find main 4-col dictionary table (**Словарь:** + Кандзи|Хирагана|Ромадзи header)."""
    for i, l in enumerate(sec):
        if l.strip() == "**Словарь:**":
            for j in range(i + 1, min(i + 7, len(sec))):
                if "Кандзи" in sec[j] and "Хирагана" in sec[j] and "Ромадзи" in sec[j]:
                    k = j + 1
                    rows = []
                    while k < len(sec) and sec[k].strip().startswith("|"):
                        cells = [c.strip() for c in sec[k].strip().strip("|").split("|")]
                        if len(cells) >= 4 and not cells[0].startswith("---"):
                            rows.append((cells[0], cells[1], cells[2], cells[3]))
                        k += 1
                    return (i, k - 1, rows)
    return (None, None, [])

def find_prompt_block(sec):
    for i, l in enumerate(sec):
        if l.strip().startswith("**Промпт:**"):
            stub = "Скопируй структуру" in l
            j = i + 1
            if j < len(sec) and sec[j].strip().startswith("```"):
                j += 1
                while j < len(sec) and not sec[j].strip().startswith("```"):
                    j += 1
                j += 1
            return (i, j, stub)
    return (None, None, False)

def vocab_lines(rows):
    out = []
    for kan, hira, roma, trans in rows:
        if kan == "タクシー":
            roma = "takushii"
        out.append(f"- {kan} ({hira} / {roma}) — {trans}")
    return out

PROMPT_TEMPLATE = """**Промпт:**
```
Ты — мой японский разговорный партнёр. Я изучаю N5, уровень beginner.

Сегодняшняя тема: {theme}

Словарь:
{vocab}

Правила:
1. Говори на японском (вежливая форма です/ます)
2. КАЖДУЮ японскую фразу пиши в формате: хирагана (ромадзи) — перевод на русский.
   Пример: おなまえはなんですか？(o-namae wa nan desu ka? — Как вас зовут?)
   Так я смогу читать текст, пока ты говоришь.
3. Используй слова из словаря
4. Предложения — короткие, простые (3-5 слов)
5. Если я ошибаюсь — исправляй меня и объясняй на русском
6. Если я отвечаю правильно — постепенно усложняй: добавляй новые слова, задавай уточняющие вопросы
7. ПРОИЗНОШЕНИЕ: говори по-японски как носитель — чисто, естественно, без иностранного (русского/английского) акцента, стандартное произношение. В голосовом режиме читай японский текст (кандзи/хирагана), НЕ читай ромадзи буквально — ромадзи в скобках только для моего понимания. Пример: わたし читай «вата-щи», а не «уоташи»
8. Начни диалог! Первая реплика — твоя.
```
"""

REVIEW_TEMPLATE = """**Промпт:**
```
Ты — мой японский разговорный партнёр. Я изучаю N5.

Сегодня — день ПОВТОРЕНИЯ: {theme}

Правила:
1. Говори на японском (вежливая форма です/ます)
2. КАЖДУЮ японскую фразу пиши в формате: хирагана (ромадзи) — перевод на русский.
   Пример: おなまえはなんですか？(o-namae wa nan desu ka? — Как вас зовут?)
3. Используй пройденную лексику и грамматику (прошедшее время ました, ています, ません, 〜たい, 〜てください, 〜から, 〜より)
4. Если я ошибаюсь — исправляй меня и объясняй на русском
5. Если я отвечаю правильно — постепенно усложняй
6. ПРОИЗНОШЕНИЕ: говори по-японски как носитель — чисто, естественно, без иностранного (русского/английского) акцента. В голосовом режиме читай японский текст (кандзи/хирагана), НЕ читай ромадзи буквально — ромадзи в скобках только для моего понимания.
7. Начни диалог! Первая реплика — твоя.
```
"""

REVIEW_DAYS = {5, 9, 14, 20, 25, 28}
TEST_DAY = 30

def day_number(header):
    m = re.search(r"День (\d+)", header)
    return int(m.group(1)) if m else 0

out = []
for n in range(len(day_idxs) - 1):
    start, end = day_idxs[n], day_idxs[n + 1]
    sec = lines[start:end]
    header = sec[0]
    theme = get_theme(header)
    dnum = day_number(header)

    lbl_idx, after_code, is_stub = find_prompt_block(sec)

    if dnum == 1:
        out.extend(sec)
        continue

    if dnum in REVIEW_DAYS:
        if lbl_idx is not None and not is_stub:
            new_sec = sec[:lbl_idx] + [REVIEW_TEMPLATE.format(theme=theme)] + sec[after_code:]
        else:
            insert_at = None
            for i, l in enumerate(sec):
                if l.strip().startswith(("**Новые слова", "**➕ Новые слова", "**Сценарий:**", "**Полный диалог:**", "**Свободный диалог:**", "Perplexity")):
                    insert_at = i
                    break
            if insert_at is None:
                insert_at = len(sec)
            new_sec = sec[:insert_at] + [REVIEW_TEMPLATE.format(theme=theme)] + sec[insert_at:]
        out.extend(new_sec)
        continue

    if dnum == TEST_DAY:
        if lbl_idx is not None and not is_stub:
            new_sec = sec[:lbl_idx] + [REVIEW_TEMPLATE.format(theme=theme)] + sec[after_code:]
        else:
            insert_at = None
            for i, l in enumerate(sec):
                if l.strip().startswith("**Тема"):
                    insert_at = i
                    break
            if insert_at is None:
                insert_at = len(sec)
            new_sec = sec[:insert_at] + [REVIEW_TEMPLATE.format(theme=theme)] + sec[insert_at:]
        out.extend(new_sec)
        continue

    d_start, d_end, rows = find_dict_block(sec)
    vocab = "\n".join(vocab_lines(rows)) if rows else "- (слова из темы дня)"
    prompt_block = PROMPT_TEMPLATE.format(theme=theme, vocab=vocab)

    if lbl_idx is not None:
        new_sec = sec[:lbl_idx] + [prompt_block] + sec[after_code:]
    else:
        insert_at = None
        if d_end is not None:
            insert_at = d_end + 1
        else:
            for i, l in enumerate(sec):
                if l.strip().startswith(("**Новые слова", "**➕ Новые слова", "**Сценарий:**", "**Полный диалог:**")):
                    insert_at = i
                    break
            if insert_at is None:
                insert_at = len(sec)
        new_sec = sec[:insert_at] + [prompt_block] + sec[insert_at:]
    out.extend(new_sec)

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(out)

print("Done. Days processed:", len(day_idxs) - 1)
print("Total lines:", len(out))
print("Check leftover stubs: grep -n 'слова из темы дня'", PATH)
