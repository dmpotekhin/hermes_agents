#!/usr/bin/env python3
"""
Query the JLPT RAG database.
Supports: CLI search, and programmatic import for Telegram bot.
"""

import json
import os
import sys

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = '/Users/dmitrypotekhin/Downloads/jp_rag_data/chromadb/'
MODEL_INFO = json.load(open(os.path.join(CHROMA_PATH, 'model_info.json')))

# Load model once
_model = None
_collection = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading model: {MODEL_INFO['embed_model']}", file=sys.stderr)
        _model = SentenceTransformer(MODEL_INFO['embed_model'])
    return _model

def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection('jlpt_patterns')
    return _collection


def search(query, jlpt_level=None, n_results=5):
    """
    Search the RAG database.
    
    Args:
        query: Search query in any language (Japanese, English, Russian)
        jlpt_level: Optional filter ('N5', 'N4', 'N3', 'N2', 'N1') or None for all
        n_results: Number of results to return
    
    Returns:
        List of dicts with pattern info
    """
    model = get_model()
    collection = get_collection()

    # Encode query with e5 prefix
    query_emb = model.encode(f"query: {query}", normalize_embeddings=True)

    # Build filter if level specified
    where = None
    if jlpt_level:
        where = {'jlpt_level': jlpt_level.upper()}

    results = collection.query(
        query_embeddings=query_emb.tolist(),
        n_results=n_results * 2,  # fetch extra, filter if needed
        where=where,
    )

    # Parse results
    output = []
    for i in range(len(results['ids'][0])):
        doc_id = results['ids'][0][i]
        distance = results['distances'][0][i]
        meta = results['metadatas'][0][i]

        # Full pattern data
        full_data = json.loads(meta['full_data'])

        output.append({
            'id': doc_id,
            'jlpt_level': meta['jlpt_level'],
            'pattern_title': meta['pattern_title'],
            'meaning': meta['meaning'],
            'formation': meta['formation'],
            'score': 1 - distance,  # cosine similarity
            'japanese_examples': full_data['japanese_examples'],
            'english_examples': full_data['english_examples'],
            'hiragana_examples': full_data['hiragana_examples'],
            'romaji_examples': full_data['romaji_examples'],
            'vocabulary': full_data['vocabulary'],
            'page_start': meta['page_start'],
            'page_end': meta['page_end'],
        })

    # Sort by score
    output.sort(key=lambda x: x['score'], reverse=True)
    return output[:n_results]


def format_result(p, include_details=True):
    """Format a pattern result for display."""
    lines = []
    lines.append(f"━━━ {p['pattern_title']} ━━━")
    lines.append(f"  JLPT {p['jlpt_level']}  |  стр. {p['page_start']}-{p['page_end']}")
    lines.append(f"  Релевантность: {p['score']:.2%}")
    
    if p['meaning']:
        lines.append(f"\n📖 {p['meaning'][:200]}")
    
    if p['formation']:
        lines.append(f"\n🔧 Формула: {p['formation']}")
    
    if p['japanese_examples']:
        lines.append(f"\n🇯🇵 Примеры:")
        for ex in p['japanese_examples'][:3]:
            lines.append(f"   {ex}")
    
    if p['english_examples']:
        lines.append(f"\n🇬🇧 Перевод:")
        for ex in p['english_examples'][:3]:
            lines.append(f"   {ex}")
    
    if p['hiragana_examples'] and include_details:
        lines.append(f"\n🔤 Хирагана:")
        for ex in p['hiragana_examples'][:2]:
            lines.append(f"   {ex}")
    
    if p['vocabulary'] and include_details:
        lines.append(f"\n📝 Слова:")
        for v in p['vocabulary'][:5]:
            lines.append(f"   {v['word']} ({v['reading']}) — {v['meaning']}")
    
    return '\n'.join(lines)


def format_simple(p):
    """Compact format for quick display."""
    emoji = {'N5': '🟢', 'N4': '🔵', 'N3': '🟡', 'N2': '🟠', 'N1': '🔴'}
    lv = emoji.get(p['jlpt_level'], '⚪')
    title = p['pattern_title'][:50]
    meaning = p['meaning'][:80] if p['meaning'] else ''
    return f"{lv} {p['jlpt_level']} | {title}\n   {meaning}"


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 query_rag.py '<query>' [N5|N4|N3|N2|N1]")
        print("Example: python3 query_rag.py 'частица は' N5")
        sys.exit(1)

    query = sys.argv[1]
    level = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"🔍 Поиск: '{query}'" + (f" (уровень {level})" if level else ""))
    print()

    results = search(query, jlpt_level=level, n_results=5)

    if not results:
        print("Ничего не найдено.")
        sys.exit(0)

    print(f"Найдено {len(results)} результатов:\n")
    for i, p in enumerate(results):
        print(format_result(p, include_details=(i < 3)))
        print()
