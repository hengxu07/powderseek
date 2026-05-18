# Powderseek — Product Requirements Document

## Problem

Planning a ski or snowboard trip requires manually checking forecasts across many resorts, mentally weighing travel time, snow quality, and budget — with no tool that does this reasoning for you. OpenSnow gives great forecasts but you still have to scan every resort yourself. The decision of *where to go* — especially when you're open to flying — is entirely on the user.

## Solution

An AI-powered trip planner that answers one question: **"I have X days free starting [date] — where should I go for the best snow?"**

The agent pulls live forecasts, factors in travel time from your home airport, and recommends the optimal resort for your trip length, skill level, terrain preference, and budget. For longer trips it goes global — Japan, Switzerland, New Zealand, Chile — and explains *why* a destination is worth the journey.

---

## Users

**Primary**: Southern California skiers/snowboarders (OC, LA, SD) who already know how to ski and take 2–10 day ski trips per season. Comfortable flying for the right trip.

**Secondary**: Anyone in the US planning a ski trip who's open to data-driven destination recommendations.

---

## Core User Flows

### 1. Weekend trip (2–3 days)
> "It's Thursday. I want to ski this weekend. Where should I go?"

Agent checks SoCal resorts + Mammoth. Recommends based on who got snow this week. If everything is flat, it says so and suggests waiting or doing a groomer day locally.

### 2. Short trip (4–5 days)
> "I have Presidents' Week off. Where's skiing best right now — open to flying domestic."

Agent opens up Utah (Alta, Snowbird, Park City) and Colorado (Breckenridge, Telluride). Compares forecasts, ranks by snow + travel overhead. Suggests a primary pick and a backup.

### 3. Destination trip (7+ days)
> "I'm taking 10 days in February. Surprise me."

Agent pitches Japan (Niseko), Switzerland (Verbier), or Canada (Whistler) depending on forecast + user vibe. Explains the full experience — culture, food, terrain character — not just snowfall numbers.

### 4. Planning ahead
> "I'm flexible in January. Which 2-week window looks best for powder at Alta?"

Agent uses historical reliability data to advise on timing, noting that forecast accuracy drops beyond 7 days.

---

## Features

### MVP
- [ ] Conversational chat interface (streaming)
- [ ] Trip tier classification (day / weekend / short / medium / long / expedition)
- [ ] Live snow forecast via Open-Meteo API (lat/lon for each resort)
- [ ] Resort database (25–30 resorts across all tiers)
- [ ] Flight route lookup table (SNA + LAX → major ski hubs)
- [ ] Scoring and ranking (snow + travel efficiency + terrain + budget)
- [ ] Agent recommendation with natural language explanation
- [ ] User profile persistence (skill level, home airport, terrain preference, budget)

### V2
- [ ] "Watch mode" — user sets a trip window, agent alerts when powder forecasts spike
- [ ] Multi-resort itinerary (e.g. Park City Day 1–3, Snowbird Day 4–5)
- [ ] Pass awareness — prioritize resorts covered by user's Ikon or Epic pass
- [ ] Flight price integration (Google Flights API or ITA Matrix)
- [ ] Mobile app (PWA or React Native)
- [ ] Southern Hemisphere flip (auto-recommend NZ/Chile/Argentina June–September)

### Out of scope (for now)
- Hotel/lodging booking
- Lift ticket booking
- Avalanche / backcountry safety data
- Real-time lift status

---

## Success Metrics

| Metric | Target (3 months) |
|---|---|
| Recommendations served | 500/month |
| Return sessions per user | ≥ 2 |
| Agent satisfaction (thumbs up) | ≥ 70% |
| Forecast cache hit rate | ≥ 80% |

---

## Constraints

- Open-Meteo is free up to 10,000 calls/day — more than enough for MVP
- OpenSnow has no public API — we rely on weather models, not their proprietary blend
- Flight prices are not included in MVP — user handles their own booking
- Resort database is manually curated — no automated scraping

---

## Non-Goals

- This is not a booking platform
- This is not trying to replace OpenSnow (we use weather APIs, not snow reporters)
- This is not a social app
