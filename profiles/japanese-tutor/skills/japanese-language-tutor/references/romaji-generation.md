# Romaji Generation from Hiragana

## Algorithm

Convert hiragana to romaji via a lookup table. Priority: longest match first
(3-char combo → 2-char combo → single char).

### Handling っ (small tsu)

When っ is encountered, double the first consonant of the next syllable:

```
あった → atta  (a + っ + ta → a + t + ta)
いっしょ → issho  (i + っ + sho → i + s + sho)
```

### Vowel elongation

- `ou`/`oo` → `ō` (e.g., おおきい → ōkii)
- `uu` → `ū` (e.g., くうき → kūki)
- `ei` → `ē` (e.g., せんせい → sensē)
- `ii` → `ī` (e.g., おいしい → oishī)

### Katakana → Hiragana

Convert katakana to hiragana first (`chr(ord(catakana_char) - 96)`) before
running romaji generation.

## Full Mapping Table

### 46 Base Characters (gojūon)

| あ a | い i | う u | え e | お o |
| か ka | き ki | く ku | け ke | こ ko |
| さ sa | し shi | す su | せ se | そ so |
| た ta | ち chi | つ tsu | て te | と to |
| な na | に ni | ぬ nu | ね ne | の no |
| は ha | ひ hi | ふ fu | へ he | ほ ho |
| ま ma | み mi | む mu | め me | も mo |
| や ya | ゆ yu | よ yo |
| ら ra | り ri | る ru | れ re | ろ ro |
| わ wa | を wo | ん n |

### Dakuten / Handakuten (voiced)

| が ga | ぎ gi | ぐ gu | げ ge | ご go |
| ざ za | じ ji | ず zu | ぜ ze | ぞ zo |
| だ da | ぢ ji | づ zu | で de | ど do |
| ば ba | び bi | ぶ bu | べ be | ぼ bo |
| ぱ pa | ぴ pi | ぷ pu | ぺ pe | ぽ po |

### Yōon (contracted)

| きゃ kya | きゅ kyu | きょ kyo |
| しゃ sha | しゅ shu | しょ sho |
| ちゃ cha | ちゅ chu | ちょ cho |
| にゃ nya | にゅ nyu | にょ nyo |
| ひゃ hya | ひゅ hyu | ひょ hyo |
| みゃ mya | みゅ myu | みょ myo |
| りゃ rya | りゅ ryu | りょ ryo |

| ぎゃ gya | ぎゅ gyu | ぎょ gyo |
| じゃ ja | じゅ ju | じょ jo |
| びゃ bya | びゅ byu | びょ byo |
| ぴゃ pya | ぴゅ pyu | ぴょ pyo |

### Python Implementation

```python
ROMAJI_MAP = {
    'あ':'a','い':'i','う':'u','え':'e','お':'o',
    'か':'ka','き':'ki','く':'ku','け':'ke','こ':'ko',
    'さ':'sa','し':'shi','す':'su','せ':'se','そ':'so',
    'た':'ta','ち':'chi','つ':'tsu','て':'te','と':'to',
    'な':'na','に':'ni','ぬ':'nu','ね':'ne','の':'no',
    'は':'ha','ひ':'hi','ふ':'fu','へ':'he','ほ':'ho',
    'ま':'ma','み':'mi','む':'mu','め':'me','も':'mo',
    'や':'ya','ゆ':'yu','よ':'yo',
    'ら':'ra','り':'ri','る':'ru','れ':'re','ろ':'ro',
    'わ':'wa','を':'wo','ん':'n',
    'が':'ga','ぎ':'gi','ぐ':'gu','げ':'ge','ご':'go',
    'ざ':'za','じ':'ji','ず':'zu','ぜ':'ze','ぞ':'zo',
    'だ':'da','ぢ':'ji','づ':'zu','で':'de','ど':'do',
    'ば':'ba','び':'bi','ぶ':'bu','べ':'be','ぼ':'bo',
    'ぱ':'pa','ぴ':'pi','ぷ':'pu','ぺ':'pe','ぽ':'po',
    'ー':'-',
    'きゃ':'kya','きゅ':'kyu','きょ':'kyo',
    'しゃ':'sha','しゅ':'shu','しょ':'sho',
    'ちゃ':'cha','ちゅ':'chu','ちょ':'cho',
    'にゃ':'nya','にゅ':'nyu','にょ':'nyo',
    'ひゃ':'hya','ひゅ':'hyu','ひょ':'hyo',
    'みゃ':'mya','みゅ':'myu','みょ':'myo',
    'りゃ':'rya','りゅ':'ryu','りょ':'ryo',
    'ぎゃ':'gya','ぎゅ':'gyu','ぎょ':'gyo',
    'じゃ':'ja','じゅ':'ju','じょ':'jo',
    'びゃ':'bya','びゅ':'byu','びょ':'byo',
    'ぴゃ':'pya','ぴゅ':'pyu','ぴょ':'pyo',
}
```

**Note:** This reference was created 2026-07-08 during bulk N5 vocab addition
(438 words, user_vocab.json → 929 total).
