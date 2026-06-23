---
name: flight-search
description: Comprehensive flight search and travel planning — multi-source aggregation, airport alternatives, price comparison, and structured presentation.
tags: [travel, flights, booking, comparison]
---

# Flight Search & Travel Planning

Systematic workflow for finding the best flight deals and presenting them clearly to the user on Telegram.

## When to Load
- The user asks for flight ticket search or price comparison
- The user wants travel recommendations (destinations, timing, routing)
- The user needs baggage/airport/visa information for a specific route
- The user is comparing airline options

## Workflow

### 1. Clarify (if vague)
If the user gives an open-ended request ("I want to go somewhere warm", "find me cheap tickets to Europe"), ask:
- **Budget** (per person or total)
- **Dates** (exact or flexible range)
- **Preferences** (direct vs connecting, baggage vs no baggage, comfort vs budget)
- **Number of passengers**
- **Departure city / airports** (note all major airports)

### 2. Search Strategy — Multi-Source

Use **at least 3 different search approaches** in parallel:

| Approach | Tools | Notes |
|---|---|---|
| Aggregators | `web_search` for Aviasales, Trip.com, Skyscanner | Fast, broad price overview |
| Airline direct | `web_search` for airline name + route | Turkish Airlines, Pobeda, AJet, Pegasus, Southwind |
| Browser | `browser_navigate` to Google Flights, Aviasales | For specific date searches (more prone to captchas) |

**Common Aggregators for Russia/Turkey routes:**
- `aviasales.ru` — best for Russian-speaking users, shows RUB prices
- `trip.com` — international, shows $ and RUB
- `kupi.com` — English-friendly, good overview
- `flypobeda.ru` — Pobeda's direct site
- `turkishairlines.com` — Turkish Airlines direct
- `ajet.com` — AJet (VKO→SAW)
- `skyscanner.com` — global comparison

**Captcha handling**: Aviasales frequently blocks with Yandex SmartCaptcha. Google Flights requires cookie consent. When blocked:
- Pivot to other aggregators (Trip.com, kupi.com, airline direct sites)
- Use `web_search` queries with airline + route + date patterns instead
- Try `web_extract` on static pages that summarise pricing

### 3. Query Patterns

```text
# General price level
"{airline}" "{from}" "{to}" "{month} {year}" price

# Specific dates
flights "{from}" to "{to}" "{date}" round trip

# Russian-language patterns
авиабилеты {from} {to} {date} цена

# Reverse direction (return flight)
flights "{to}" to "{from}" "{return_date}"
```

### 4. Compare & Structure

For each option, capture:
- **Airline** (+ baggage policy)
- **Route** (airports — note SVO/DME/VKO/ZIA for Moscow, IST/SAW for Istanbul)
- **Flight time** + duration
- **Number of stops** (direct vs connecting)
- **Price** (one-way and/or round-trip)
- **Baggage included?** (critical for low-cost carriers)

### 5. Present in Telegram-Optimized Format

Use structured markdown with:
- **Emoji headers** for visual scanning (🛫🛬💵✅❌)
- **Markdown tables** for side-by-side comparison
- **🏆 medal system** for ranking options
- **Separate sections** for: options, airport info, destination tips
- **Pros/cons** per option — be honest about drawbacks
- End with a **recommendation** based on likely user needs

**Price presentation:**
- Prefer RUB for Russian-speaking users
- Convert from $/€ at ~100 RUB/USD approximate rate
- Always show price ranges, not exact single prices
- Note whether baggage is included

### 6. Add Destination Value

After finding flights, always suggest **2-4 must-see attractions or activities** at the destination. This completes the travel-planning experience.

### 7. Close Loop

End with a question: offer to check specific dates/flights, or ask about baggage needs, or suggest alternative dates that might be cheaper.

## Pitfalls

- **Pobeda (Победа)**: ultra-low base fares but NO free checked baggage. Hand luggage strict: 36×30×27 cm, 10 kg. Baggage adds ~3,000-5,000 RUB each way. Aggressive gate sizer checks.
- **Currency confusion**: International sites show $ or €. Use approximate RUB conversion (~100 RUB = $1) but clarify this is an estimate.
- **Price freshness**: Flight prices change hourly. Always note "цены на момент поиска" disclaimer.
- **July is peak season**: Moscow→Turkey in July is high demand. Book at least 2-4 weeks ahead.
- **Two Istanbul airports**: **IST** (new airport, European side — better location, major airlines) vs **SAW** (Sabiha Gökçen, Asian side — used by low-cost carriers like Pegasus, AJet). Always note which airport the flight arrives at.
- **Visa**: Turkish e-Visa is quick and cheap (~$60, online) for Russian passport holders. Confirm if needed.
- **Aviasales captcha**: Will show Yandex SmartCaptcha after clicking "Найти билеты". Workaround: search other aggregators instead of fighting captcha.
