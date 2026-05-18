# Powderseek — Architecture

## Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React + Vite | Same as Namicast — familiar, fast |
| Backend | FastAPI (Python) | Async, easy Claude API integration |
| Database | PostgreSQL | Structured resort/forecast data, user profiles |
| AI | Claude API (claude-sonnet-4-6) | Conversational reasoning + trip recommendations |
| Forecast | Open-Meteo API | Free, global, lat/lon snow forecasts |
| Hosting (API) | Railway | Same as Namicast |
| Hosting (Frontend) | Vercel | Same as Namicast |

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        Browser                           │
│                                                          │
│   React Chat UI                                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │  Trip input (dates, origin, preferences)        │   │
│   │  Streaming chat (SSE)                           │   │
│   │  Recommendation card + resort details          │   │
│   └─────────────────────────────────────────────────┘   │
└───────────────────────┬──────────────────────────────────┘
                        │ HTTPS / SSE
┌───────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                        │
│                                                          │
│  POST /chat          — main conversation endpoint        │
│  GET  /resorts       — browse resort list                │
│  GET  /forecast/{id} — current forecast for one resort   │
│  POST /profile       — save user preferences             │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  routing.py                                     │    │
│  │  classify_tier() → filter_reachable() →         │    │
│  │  score_resort()  → rank_resorts()               │    │
│  │  build_agent_prompt()                           │    │
│  └──────────────────────┬──────────────────────────┘    │
│                         │                               │
│  ┌──────────────────────▼──────────────────────────┐    │
│  │  Claude Agent (claude-sonnet-4-6)               │    │
│  │                                                 │    │
│  │  System prompt: trip context + ranked resorts   │    │
│  │  Tools:                                         │    │
│  │    get_forecast(resort_id)   — fetch fresh data │    │
│  │    get_resort_details(slug)  — full resort info  │    │
│  │    save_preference(key, val) — update profile   │    │
│  │                                                 │    │
│  │  Streams response via SSE                       │    │
│  └─────────────────────────────────────────────────┘    │
└──────────┬────────────────────────────┬─────────────────┘
           │                            │
┌──────────▼──────────┐    ┌────────────▼────────────────┐
│     PostgreSQL       │    │      Open-Meteo API          │
│                      │    │                              │
│  resorts             │    │  /forecast?lat=&lon=         │
│  flight_routes       │    │  &daily=snowfall_sum         │
│  snow_forecasts      │    │  &hourly=snow_depth          │
│  user_profiles       │    │                              │
│  conversations       │    │  Called by forecast worker   │
│  trips               │    │  (background job, 6hr cycle) │
└──────────────────────┘    └─────────────────────────────┘
```

---

## Data Flow: Chat Request

```
1. User sends message ("I have 5 days in February, where should I go?")

2. Backend:
   a. Load user profile (session_id)
   b. Parse trip intent → duration_days, start_date, origin_airport
   c. classify_tier() → TripTier.SHORT
   d. Load reachable resorts from DB (filtered by continent/country for this tier)
   e. Load latest snow_forecasts for those resorts
   f. filter_reachable() → drops resorts outside travel constraints
   g. score_resort() → rank_resorts() → top 5
   h. build_agent_prompt() → structured context block

3. Claude Agent:
   a. Receives system prompt (trip context + top 5 resorts)
   b. Receives conversation history
   c. May call get_forecast() tool for fresher data or more resort detail
   d. Streams recommendation back via SSE

4. Frontend renders streaming response in chat bubble
```

---

## Forecast Cache Strategy

Open-Meteo is called by a **background worker**, not on-demand per chat:

- All ~30 resorts refreshed every **6 hours**
- Forecasts stored in `snow_forecasts` table with `fetched_at` timestamp
- Chat endpoint reads from cache — no latency hit during conversation
- Worker runs as a Railway cron job (or APScheduler within the FastAPI process for MVP)

This mirrors Namicast's pre-computation pattern for the default spots.

---

## Agent Tools

| Tool | Purpose |
|---|---|
| `get_forecast(resort_id)` | Returns latest cached forecast for a specific resort |
| `get_resort_details(slug)` | Returns full resort record (agent_notes, terrain, vibe tags) |
| `save_preference(key, value)` | Persists a user preference to their profile mid-conversation |
| `compare_resorts(slugs[])` | Returns side-by-side forecast + metadata for a list of resorts |

---

## Key Differences from Namicast

| | Namicast | Powderseek |
|---|---|---|
| Data source | Stormglass (ocean buoys) | Open-Meteo (atmospheric model) |
| Recommendation scope | Fixed spots near user | Global, tier-based |
| Trip planning | None (real-time conditions) | Core feature — dates, duration, travel |
| Agent complexity | Tool-use + SSE streaming | Same + routing/scoring pre-pass before agent |
| Database | Single surf spots table | Resorts + flight_routes + richer metadata |

---

## Directory Structure

```
powderseek/
├── app/
│   ├── main.py           — FastAPI app, routes
│   ├── routing.py        — tier classification, scoring, prompt builder
│   ├── agent.py          — Claude API integration, tool definitions, SSE stream
│   ├── forecast.py       — Open-Meteo client + cache refresh worker
│   ├── db.py             — PostgreSQL connection, query helpers
│   └── models.py         — Pydantic models for request/response
├── db/
│   ├── schema.sql
│   └── seed_resorts.sql
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── TripInput.tsx
│   │   │   └── ResortCard.tsx
│   │   └── hooks/
│   │       └── useChat.ts    — SSE streaming hook
│   └── vite.config.ts
├── PRD.md
├── ARCHITECTURE.md
└── README.md
```
