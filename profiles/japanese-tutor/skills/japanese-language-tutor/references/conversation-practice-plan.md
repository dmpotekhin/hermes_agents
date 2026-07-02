# 30-Day Conversational Practice Plan

## Purpose

Structured plan for dialogue-based speaking practice. Each day = one theme with:
- Vocabulary table (kanji | hiragana | romaji | Russian)
- Grammar focus
- Dialogue scenario
- Self-contained prompt for external AI (Perplexity, Claude, etc.)

## Target Level

JLPT N5 → N4 bridge. Progressive difficulty over 6 weeks.

## Structure

| Week | Days | Focus | Grammar |
|------|------|-------|---------|
| 1 | 1-5 | Basic introductions, family, food, hobbies | です/ます, の, は, が, を, ある/いる |
| 2 | 6-10 | Descriptions, daily routine, shopping, people | い-adj, な-adj, 〜から〜まで, ください |
| 3 | 11-15 | Invitations, requests, comparisons, plans | ませんか, てください, より, つもり |
| 4 | 16-20 | Reasons, restaurant, city, seasons | から, ので, とき, ほうがいい |
| 5 | 21-25 | Travel, health, opinions, choices | たことがある, 〜たい, 〜と思う |
| 6 | 26-30 | Past experience, news, future, phone, final test | 〜たり〜たり, そうだ, かもしれない |

## Prompt Format for External AI

### Global Instruction (send once before Day 1):

```
Ты — Сато-сенсей, японский репетитор. Формат ответа:
- Каждое слово/фраза — в таблице | Кандзи | Хирагана | Ромадзи | Перевод на русский |
- После каждой реплики ученика — исправление ошибок
- После 3-4 реплик — пауза с итогом
- Объяснения на русском
- Тон — тёплый, ободряющий

Структура дня:
1. Словарь темы (таблица)
2. Сценарий диалога
3. Первая реплика AI на японском
4. После каждого ответа — исправление + 1-2 новых слова
5. В конце — сводная таблица новых слов
```

### Daily Prompt Template:

```
Sato-sensei, день N — [Theme]
[Context about the student]
[Grammar focus]
Start the dialogue! [First line hint]
```

## Key Design Decisions

1. **Self-contained prompts** — each day carries its own vocabulary and scenario
2. **Error correction baked in** — AI told to correct after every student reply
3. **4-column vocabulary** — kanji | hiragana | romaji | Russian (student's preference)
4. **Review every 5th day** — spiral repetition
5. **Role-play scenarios** — real-life situations (restaurant, phone, doctor)
6. **Student profile embedded** — uses real facts (Pekin 8 years, software tester, 山田)

## Week-by-Week Topics

See the master file at `~/.hermes/jp_rag_data/30_days_conversation_prompts.md` for full prompts.

### Week 1 — Basic Communication
- Day 1: Self-introduction (はじめまして)
- Day 2: Family (家族)
- Day 3: Food & drinks (食べ物・飲み物)
- Day 4: Hobbies (趣味)
- Day 5: Review — mixed conversation

### Week 2 — Descriptions & Daily Life
- Day 6: Weather (天気)
- Day 7: Daily routine (一日)
- Day 8: Shopping (買い物)
- Day 9: Describing people (人の形容)
- Day 10: Review — weekend story

### Week 3 — Requests, Plans, Comparisons
- Day 11: Invitations (誘う)
- Day 12: Requests & permission (依頼・許可)
- Day 13: Comparisons (比較)
- Day 14: Weekend plans (週末の予定)
- Day 15: Review — tourist asking directions

### Week 4 — Reasons, Stories
- Day 16: Reasons & explanations (理由)
- Day 17: Restaurant full dialogue (レストラン)
- Day 18: My city (私の町)
- Day 19: Weather & seasons (天気と季節)
- Day 20: Review — hotel phone call

### Week 5 — Free Conversations
- Day 21: Travel (旅行)
- Day 22: Health (健康)
- Day 23: Opinions & gifts (意見・プレゼント)
- Day 24: Choices & dilemmas (選択)
- Day 25: Review — free topic chosen by AI

### Week 6 — Final Dialogues
- Day 26: Past experience (経験)
- Day 27: News summary (ニュース)
- Day 28: Future plans (将来の計画)
- Day 29: Phone call (電話)
- Day 30: Final test — 10-15min free dialogue with assessment
