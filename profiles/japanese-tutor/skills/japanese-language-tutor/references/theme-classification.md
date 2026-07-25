# Theme Classification for N5 Vocabulary

## Приоритет проверки (first-match wins)

При автоматическом назначении темы слову — проверять в этом порядке:

1. время → еда → семья → дом → места → природа → здоровье → вещи → работа → профессии → хобби → языки → вопросы → наречия → прилагательные → числа → глаголы → дом (catch-all)

## Детекторы по темам

### время
- English keywords: o'clock, minute, hour, day of week, week, month, year, morning, evening, tonight, today, yesterday, tomorrow, every day, every week, every month, every year, every morning, every night, this week, last week, next week, this month, last month, next month, this year, last year, next year, sometimes, always, usually, now, then, later, after, before, soon, recently, spring, summer, autumn, fall, winter, season, time, when, what time, already
- Kanji: 今日, 昨日, 明日, 明後日, 毎日, 毎週, 毎月, 毎年, 毎朝, 毎晩, 今週, 来週, 先週, 今月, 来月, 先月, 今年, 去年, 来年, 朝, 昼, 夜, 晩, 午前, 午後, 今朝, 今晩, 昨夜, 夕べ, 春, 夏, 秋, 冬, 季節, 先日, 最近, 以前, 以降, 月曜日, 火曜日, 水曜日, 木曜日, 金曜日, 土曜日, 日曜日, 何曜日, 曜日

### еда
- English keywords: food, drink, eat, delicious, breakfast, lunch, dinner, rice, bread, water, tea, coffee, sweet, spicy, bitter, sour, cook, cooking, restaurant, vegetable, fruit, meat, fish, soup, cake, egg, milk, juice, beer, wine, alcohol, hungry, thirsty
- Kanji: ご飯, 朝ご飯, 昼ご飯, 晩ご飯, 食べ物, 飲み物, お茶, コーヒー, 牛乳, 水, 酒, ビール, ジュース, 野菜, 果物, 肉, 魚, 卵, パン, 米, 味噌, 醤油, 砂糖, 塩, 弁当, 昼食, 夕食, 朝食, 料理

### семья
- English keywords: father, mother, brother, sister, parent, grandparent, grand... , aunt, uncle, cousin, family, child, children, son, daughter, husband, wife
- Kanji: 父, 母, 兄, 姉, 弟, 妹, 祖父, 祖母, 家族, 両親, 親, 子供, 息子, 娘, 夫, 妻, 主人, 奥さん, お父さん, お母さん, お兄さん, お姉さん, 弟さん, 妹さん, 兄弟

### дом
- English keywords: house, home, apartment, room, kitchen, bathroom, toilet, bed, chair, table, desk, window, door, key, tv, television, refrigerator, clean, washing, furniture
- Kanji: 家, 部屋, 玄関, 台所, 浴室, トイレ, ベッド, 机, 椅子, 本棚, 窓, ドア, 鍵, 電気, エアコン, 冷蔵庫, テレビ, 掃除, 洗濯

### места
- English keywords: school, hospital, station, bank, library, park, shop, store, company, office, factory, temple, shrine, city, town, village, country, world, post office, museum, theater, restaurant, there, over there
- Kanji: 学校, 病院, 駅, 銀行, 郵便局, 図書館, 公園, 店, 会社, 工場, 神社, 寺, 市, 町, 村, 国, 世界, 東京, 京都, 大阪

### природа
- English keywords: weather, rain, snow, wind, cloud, sky, sea, ocean, mountain, river, forest, flower, tree, sun, moon, star, nature, typhoon, earthquake, storm, thunder, rainy, sunny, cloudy, hot, cold, warm, cool, temperature
- Kanji: 天気, 雨, 雪, 風, 雲, 空, 海, 山, 川, 森, 花, 木, 太陽, 月, 星, 曇り, 晴れ, 台風, 地震

### здоровье
- English keywords: head, hand, foot, eye, ear, mouth, nose, body, hair, face, finger, neck, shoulder, back, stomach, leg, arm, knee, pain, hurt, ache, medicine, pill, health, ill, sick, fever, cold, cough, wound, doctor, nurse, patient
- Kanji: 頭, 手, 足, 目, 耳, 口, 鼻, 体, 髪, 顔, 指, 首, 肩, 背中, お腹

### вещи (objects, clothes, transport)
- Clothes keywords: clothes, shirt, pants, trouser, shoe, hat, cap, glasses, watch, ring, umbrella, belt, tie, sock, skirt, dress, jacket, coat, uniform
- Clothes kanji: 服, 洋服, 着物, 靴, 帽子, 眼鏡, 時計, 指輪, 傘
- Objects keywords: pencil, pen, book, notebook, bag, box, letter, card, stamp, paper, map, ticket, money, coin, phone, computer, camera, key, cup, glass, bowl, chopstick, knife, fork, spoon, towel, soap, brush, mirror, lamp, radio, toy
- Transport keywords: car, train, bus, taxi, bicycle, bike, airplane, plane, ship, boat, subway, vehicle, traffic, drive, ride, station, airport, port

### работа
- English keywords: job, work, company, boss, colleague, coworker, salary, salaryman, business, office, employee, manager, president, retire, vacation, holiday, day off, break

### профессии
- English keywords: doctor, teacher, lawyer, driver, cook, chef, accountant, police, pilot, nurse, dentist, engineer, programmer, secretary, student, professor, scientist, actor
- Kanji: 先生, 医者, 看護師, 教師, 弁護士, 運転手, 料理人, 会計士, 警官, 議員, 消防士, 店員, 社長, 部長, 課長

### хобби
- English keywords: hobby, music, movie, film, book, reading, travel, photo, photograph, sport, soccer, football, baseball, tennis, swim, swimming, game, anime, manga, song, dance, singing, fishing, hiking, cycling, running, painting

### языки
- English keywords: language, japanese, english, chinese, korean, russian, french, spanish, german
- Hiragana suffix: `ご` at end of reading

### вопросы
- English keywords: how much, how many, how old, which, whose, what, who, where, when, why
- Kanji: 何, 誰, どこ, いつ, なぜ, どうして, いくら, いくつ, どの, どんな, どちら, どれ, どう, なんで

### наречия
- English keywords: always, usually, sometimes, never, already, still, yet, very, a little, a lot, more, most, also, only, just, quite, gradually, immediately, again, perhaps, maybe, probably, straight, directly
- Kanji/hiragana exact match: 全部, 多分, まっすぐ, 一番, また, すぐ, ずっと, ほとんど, やっと, そろそろ, たまに, よく, だいたい, たいてい, めったに

### прилагательные
- Rule: ends with `い` (and not `くない`) + English keyword match
- English keywords: blue, red, white, black, big, small, high, low, long, short, new, old, good, bad, hot, cold, warm, cool, early, fast, slow, busy, painful, bright, dark, tall, expensive, cheap, young, interesting, fun, boring, difficult, easy, important, dirty, clean, narrow, wide, thick, thin, heavy, light
- Color nouns without `い`: 青, 赤, 白, 黒, 茶色, 黄色, 緑, 灰色 → прилагательные
- English keyword 'adjective' or 'color'

### числа
- English keywords: hundred, thousand, ten thousand, yen, number, one, two, three, four, five, six, seven, eight, nine, ten, count, counter
- Suffixes: 個, つ, 人, 本, 枚, 匹, 冊, 杯, 階, 回, 足, 着, 歳 at end of kanji
- Kanji starts with: 〜

### глаголы
- English: starts with 'to ' or contains 'verb'
- Hiragana ending fallback: る, く, す, つ, う, む, ぶ, ぬ

### Default catch-all
→ `дом`

## Пример работы

| Выражение | Meaning | Детектор | Тема |
|-----------|---------|----------|------|
| 青 | blue | color noun → прилагательные | прилагательные |
| 青い | blue | ends with `い` + color keyword | прилагательные |
| 全部 | all, entire, whole | exact match in adverb list | наречия |
| 多分 | perhaps, probably | exact match in adverb list | наречия |
| 秋 | fall (season) | 'fall, season' in meaning | время |
| 開ける | to open (v.t.) | starts with 'to ' | глаголы |
| 朝 | morning | 'morning' in meaning | время |
| 頭 | head | 'head' in meaning | здоровье |
