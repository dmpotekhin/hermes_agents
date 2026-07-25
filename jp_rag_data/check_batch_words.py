#!/usr/bin/env python3
"""Check what useful words exist in the 438 batch for Perplexity updates, then update the plan"""
import json

with open('/tmp/n5_new_words_v2.json') as f:
    words = json.load(f)

# Find usable words by category
print("=== Verbs in 438 batch ===")
verbs = [w for w in words if w['theme'] == 'глаголы' and w['hiragana'].endswith('う')]
for w in verbs:
    print(f"  {w['kanji']:12s} | {w['hiragana']:12s} | {w['translation'][:35]}")

print("\n=== Adjectives in 438 batch ===")
adj = [w for w in words if w['theme'] == 'прилагательные']
for w in adj:
    print(f"  {w['kanji']:12s} | {w['hiragana']:12s} | {w['translation'][:35]}")

print("\n=== Time words in 438 batch ===")
time = [w for w in words if w['theme'] == 'время']
for w in time:
    print(f"  {w['kanji']:12s} | {w['hiragana']:12s} | {w['translation'][:35]}")

print("\n=== Food words in 438 batch ===")
food = [w for w in words if w['theme'] == 'еда']
for w in food:
    print(f"  {w['kanji']:12s} | {w['hiragana']:12s} | {w['translation'][:35]}")

print("\n=== Nature words in 438 batch ===")
nature = [w for w in words if w['theme'] == 'природа']
for w in nature:
    print(f"  {w['kanji']:12s} | {w['hiragana']:12s} | {w['translation'][:35]}")

print("\n=== Places in 438 batch ===")
places = [w for w in words if w['theme'] == 'места']
for w in places:
    print(f"  {w['kanji']:12s} | {w['hiragana']:12s} | {w['translation'][:35]}")

print("\n=== Things in 438 batch ===")
things = [w for w in words if w['theme'] == 'вещи']
for w in things:
    print(f"  {w['kanji']:12s} | {w['hiragana']:12s} | {w['translation'][:35]}")

print("\n=== Hobbies in 438 batch ===")
hobbies = [w for w in words if w['theme'] == 'хобби']
for w in hobbies:
    print(f"  {w['kanji']:12s} | {w['hiragana']:12s} | {w['translation'][:35]}")
