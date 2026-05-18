# Powderseek

AI-powered ski and snowboard trip planner. Tell it how many days you have and it recommends where to go — from a SoCal day trip to a 10-day Japan powder pilgrimage — based on live snow forecasts, travel time, your skill level, and budget.

**Live at [powderseek.vercel.app](https://powderseek.vercel.app)**

## How it works

1. Set your trip dates, origin airport, skill level, and budget in the trip form
2. The app classifies your trip tier (day / weekend / short / medium / long / expedition)
3. It fetches live snow forecasts for reachable resorts and scores them on snow quality, travel efficiency, terrain match, and budget fit
4. A Claude-powered agent streams a confident recommendation with honest trade-offs
5. Follow-up questions ("what's the food like?" / "compare those two") are answered in context — the agent remembers which resorts it ranked
6. Click any bold resort name in the chat to open a detail panel with a 7-day snow chart, terrain breakdown, and mountain stats

Resorts unlock by trip length: local SoCal spots for day trips, Utah/Colorado for 4–5 days, Whistler/Banff for a week, and Japan/Europe/New Zealand/Chile for 7+ days.

Ski-only resorts (Alta, Deer Valley) are flagged in the agent context and shown with a warning banner in the detail panel.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React + Vite + TypeScript |
| Backend | FastAPI (Python 3.12) |
| AI | Claude API (claude-sonnet-4-6) with tool use + SSE streaming |
| Database | PostgreSQL (asyncpg) |
| Forecasts | Open-Meteo API — free, global, refreshed every 6 hours |
| Deployment | Railway (backend + DB) + Vercel (frontend) |

## Local setup

**Prerequisites**: Python 3.12, Node 18+, PostgreSQL 16

### 1. Database

```bash
createdb powderseek
psql powderseek -f db/schema.sql
psql powderseek -f db/seed_resorts.sql
psql powderseek -f db/seed_more_resorts.sql
```

### 2. Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY and DATABASE_URL to .env

PYTHONPATH=app uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`.

## Project structure

```
powderseek/
├── app/
│   ├── main.py        — FastAPI routes, lifespan, 6-hour forecast scheduler
│   ├── agent.py       — Claude agentic loop, tool definitions, SSE streaming
│   ├── routing.py     — Trip tier classification, resort scoring, prompt builder
│   ├── db.py          — asyncpg pool, query helpers
│   ├── forecast.py    — Open-Meteo client, background refresh
│   └── models.py      — Pydantic schemas
├── db/
│   ├── schema.sql          — 6 tables: resorts, forecasts, profiles, conversations, trips
│   ├── seed_resorts.sql    — Base resorts + flight routes from SNA/LAX
│   └── seed_more_resorts.sql — Additional Japan and Europe resorts
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatWindow.tsx  — Message list, resort name→slug map, drawer state
│       │   ├── Message.tsx     — Markdown rendering, clickable resort name detection
│       │   ├── ResortDrawer.tsx — Slide-in detail panel, 7-day bar chart, terrain breakdown
│       │   ├── ChatInput.tsx   — Unified input box
│       │   └── TripInput.tsx   — Trip form (dates, airport, skill, budget)
│       └── hooks/
│           └── useChat.ts      — SSE streaming, session management
├── nixpacks.toml   — Railway build config
└── vercel.json     — Vercel build config
```

## Resort coverage

37 resorts across 5 continents, unlocked by trip length:

| Tier | Duration | Regions |
|---|---|---|
| Day trip | 1 day | SoCal (Big Bear, Snow Summit, Mt. Baldy) |
| Weekend | 2–3 days | + Mammoth, June Mountain |
| Short | 4–5 days | + Utah (Alta, Snowbird, Park City, Deer Valley) |
| Medium | 6–7 days | + Colorado (Breckenridge, Telluride, Aspen), Tahoe, Canada (Whistler, Banff, Lake Louise) |
| Long | 8–14 days | + Japan (Niseko, Hakuba, Furano, Rusutsu, Nozawa Onsen, Myoko Kogen), Europe (Chamonix, Verbier, Zermatt, Val d'Isère, St. Anton, Kitzbühel, Ischgl, Courchevel, St. Moritz, Cortina) |
| Expedition | 15+ days | + New Zealand (Queenstown, Mt. Hutt), Chile (Portillo, Valle Nevado) |

## Scoring model

Each resort is scored on four weighted components:

| Component | Weight | Signal |
|---|---|---|
| Snow quality | 45% | New snow + 7-day accumulation + base depth + historical reliability |
| Travel efficiency | 25% | Penalises resorts where travel eats too much of the trip |
| Terrain match | 15% | Overlap between user's preferred terrain and resort tags |
| Budget fit | 10% | Distance between user budget tier and resort cost tier |
