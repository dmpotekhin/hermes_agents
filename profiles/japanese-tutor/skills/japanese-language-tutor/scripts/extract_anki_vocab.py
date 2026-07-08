#!/usr/bin/env python3
"""
Extract vocabulary from an Anki .apkg deck and classify entries
as clean words vs. sentence fragments.

Output: JSON report + optional add-to-vocab JSON for the user's
user_vocab.json workflow.

Usage:
  python3 scripts/extract_anki_vocab.py <path/to/deck.apkg> [--vocab user_vocab.json]
"""
import zipfile, sqlite3, json, os, re, sys, argparse
from pathlib import Path

PARTICLE_SUFFIXES = re.compile(
    r'(は|が|を|に|で|へ|と|も|の|や|か|から|まで|だ|です|ます|'
    r'でした|ません|たい|ない|た|て|よう|ましょう|'
    r'ください|なさい|すぎる)$'
)
KANJI = re.compile(r'[\u4e00-\u9fff]')
HIRAGANA_ONLY = re.compile(r'^[\u3040-\u309fー]+$')

# Words that look like verbs but in conjugated form (not dictionary form)
# Common non-dictionary endings for N5
CONJUGATED_ENDINGS = re.compile(
    r'(ました|ません|ませんでした|ましたか|ましょう|'
    r'なかった|くなかった|だった|ではなかった|じゃなかった|'
    r'ている|ています|ていました|てる|てます|'
    r'てから|たから|'
    r'ないで|なくて|'
    r'たいです|たかった|'
    r'ください|なさい)$'
)


def extract_words_from_apkg(apkg_path: str) -> list[dict]:
    """Extract all notes from an Anki .apkg file."""
    extract_dir = Path('/tmp/apkg_extract')
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(apkg_path, 'r') as z:
        anki2 = [f for f in z.namelist() if f.endswith('.anki2')]
        if not anki2:
            raise ValueError(f"No .anki2 file found in {apkg_path}")
        z.extract(anki2[0], str(extract_dir))

    db_path = extract_dir / anki2[0]
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute('SELECT flds FROM notes')
    words = []
    for row in cursor.fetchall():
        fields = row[0].split('\x1f')
        words.append({
            'kanji': fields[0].strip() if len(fields) > 0 else '',
            'hiragana': fields[1].strip() if len(fields) > 1 else '',
            'romaji': fields[2].strip() if len(fields) > 2 else '',
            'meaning': fields[3].strip() if len(fields) > 3 else '',
            'source': fields[4].strip() if len(fields) > 4 else '',
        })

    conn.close()
    return words


def load_existing_vocab(vocab_path: str) -> tuple[set, set, list]:
    """Load existing user_vocab.json and return normalized hiragana/kanji sets."""
    with open(vocab_path, encoding='utf-8') as f:
        data = json.load(f)

    existing_hiragana = set()
    existing_kanji = set()
    for w in data.get('words', []):
        h = w['hiragana'].replace(' ', '').replace('\u3000', '')
        k = w['kanji'].replace(' ', '').replace('\u3000', '')
        existing_hiragana.add(h)
        existing_kanji.add(k)

    return existing_hiragana, existing_kanji, data


def classify_word(w: dict, existing_hiragana: set, existing_kanji: set) -> str:
    """
    Classify a word as one of:
      - 'exists'      — already in user_vocab
      - 'clean'       — real word, candidate for adding
      - 'fragment'    — sentence fragment with particles/conjugation
      - 'conjugated'  — verb in conjugated (non-dictionary) form
      - 'too_short'   — single character or empty
      - 'katakana_only' — katakana word without kanji/translation
    """
    h = w['hiragana'].replace(' ', '').replace('\u3000', '')
    k = w['kanji'].replace(' ', '').replace('\u3000', '')

    if not h or len(h) < 2:
        return 'too_short'

    if h in existing_hiragana or k in existing_kanji:
        return 'exists'

    # Particle/desu/masu suffix -> fragment
    if PARTICLE_SUFFIXES.search(h):
        return 'fragment'

    # Conjugated verb form
    if CONJUGATED_ENDINGS.search(h):
        return 'conjugated'

    # Katakana-only without translation -> probably proper noun or noise
    if not KANJI.search(k) and not w['meaning']:
        return 'katakana_only'

    # Has kanji -> likely a real word
    if KANJI.search(k):
        return 'clean'

    # Hiragana word with translation -> could be real (adverb, etc.)
    if w['meaning']:
        return 'clean'

    return 'fragment'


def assign_theme(word: dict) -> str:
    """Heuristic theme assignment for N5 words."""
    h = word['hiragana']
    k = word['kanji']
    m = word['meaning'].lower()

    # Time words
    if any(t in k for t in ['曜日', '月', '火', '水', '木', '金', '土', '日', '週', '今', '昨', '明']):
        if any(t in k for t in ['曜日', '月曜', '火曜', '水曜', '木曜', '金曜', '土曜', '日曜']):
            return 'время'
    if any(t in h for t in ['ようび', 'じかん', 'じ', 'ふん', 'ぷん', 'ねん', 'がつ', 'さい']):
        return 'время'

    # Food
    if any(t in k for t in ['食', '肉', '魚', '野菜', '果物', '飲', '酒', '茶', '牛乳']):
        return 'еда'
    if any(t in h for t in ['たべ', 'のみ', 'りょうり']):
        return 'еда'

    # Place / location
    if any(t in k for t in ['駅', '学校', '教室', '病院', '図書館', '公園', '店', '銀行', '町', '国']):
        return 'места'
    if any(t in h for t in ['えき', 'がっこう', 'びょういん', 'こうえん', 'みせ', 'ぎんこう']):
        return 'места'

    # People / professions
    if any(t in k for t in ['人', '者', '士', '師', '員', '手', 'さん']):
        if any(t in k for t in ['医', '教師', '弁護', '運転', '料理', '会計', '警官', '選手']):
            return 'профессии'
        return 'знакомство'

    # Family
    if any(t in k for t in ['父', '母', '兄', '姉', '弟', '妹', '祖父', '祖母', '夫', '妻', '息子', '娘']):
        return 'семья'

    # Verbs (end in る/く/す/つ/う/む/ぶ/ぬ)
    if h.endswith(('る', 'く', 'す', 'つ', 'う', 'む', 'ぶ', 'ぬ')):
        return 'глаголы'

    # Adjectives
    if h.endswith('い') and KANJI.search(k):
        return 'прилагательные'

    # Nature / weather
    if any(t in k for t in ['天気', '雨', '雪', '風', '空', '山', '川', '海']):
        return 'природа'
    if any(t in h for t in ['てんき', 'あめ', 'ゆき', 'かぜ', 'そら', 'やま', 'かわ', 'うみ']):
        return 'природа'

    # Default
    return 'дом'


def main():
    parser = argparse.ArgumentParser(
        description='Extract and classify vocabulary from Anki .apkg')
    parser.add_argument('apkg', help='Path to .apkg file')
    parser.add_argument('--vocab', help='Path to user_vocab.json for dedup',
                        default=None)
    parser.add_argument('--output', help='Output JSON report path',
                        default='/tmp/anki_extract_report.json')
    args = parser.parse_args()

    # Extract
    all_words = extract_words_from_apkg(args.apkg)
    print(f"Total notes in Anki: {len(all_words)}")

    # Load existing vocab if provided
    existing_hiragana, existing_kanji, user_data = set(), set(), {}
    if args.vocab and os.path.exists(args.vocab):
        existing_hiragana, existing_kanji, user_data = load_existing_vocab(args.vocab)
        print(f"Existing vocab: {user_data.get('info', {}).get('total_words', '?')} words")

    # Classify
    classified = {'exists': [], 'clean': [], 'fragment': [],
                  'conjugated': [], 'too_short': [], 'katakana_only': []}
    for w in all_words:
        cls = classify_word(w, existing_hiragana, existing_kanji)
        classified[cls].append(w)

    print(f"\n  Already exists: {len(classified['exists'])}")
    print(f"  Clean (candidate): {len(classified['clean'])}")
    print(f"  Fragment (skip): {len(classified['fragment'])}")
    print(f"  Conjugated verb (skip): {len(classified['conjugated'])}")
    print(f"  Too short (skip): {len(classified['too_short'])}")
    print(f"  Katakana only (skip): {len(classified['katakana_only'])}")

    # Report clean words with translations
    clean_with_translation = [w for w in classified['clean'] if w['meaning']]
    if clean_with_translation:
        print(f"\n=== CLEAN WORDS WITH TRANSLATION ({len(clean_with_translation)}) ===")
        for w in clean_with_translation:
            print(f"  {w['kanji']:15s} | {w['hiragana']:15s} | {w['meaning']}")

    # Assign themes to clean words for vocab addition
    for w in classified['clean']:
        w['suggested_theme'] = assign_theme(w)

    # Build report
    report = {
        'stats': {
            'total': len(all_words),
            'exists': len(classified['exists']),
            'clean': len(classified['clean']),
            'fragment': len(classified['fragment']),
            'conjugated': len(classified['conjugated']),
            'too_short': len(classified['too_short']),
            'katakana_only': len(classified['katakana_only']),
        },
        'clean_words': classified['clean'],
        'fragment_samples': classified['fragment'][:15],
        'conjugated_samples': classified['conjugated'][:15],
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nReport saved to: {args.output}")
    print(f"Clean word count: {len(classified['clean'])}")
    print(f"  → To add to user_vocab.json, pipe through add_vocab workflow")


if __name__ == '__main__':
    main()
