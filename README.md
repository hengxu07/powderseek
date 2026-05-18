# Powderseek

AI-powered ski and snowboard trip planner. Tell it how many days you have and it recommends where to go — from a SoCal day trip to a 10-day Japan powder pilgrimage — based on live snow forecasts, travel time, your skill level, and budget.

## How it works

1. You describe your trip (dates, origin airport, preferences)
2. The app classifies your trip tier (day / weekend / short / medium / long / expedition)
3. It fetches live snow forecasts for reachable resorts and scores them
4. A Claude-powered agent explains the best option and why

Resorts unlock by trip length — local SoCal spots for day trips, Utah/Colorado for 4–5 days, Whistler/Banff for a week, and Japan/Europe/New Zealand/Chile for 7+ days.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React + Vite + TypeScript |
| Backend | FastAPI (Python 3.12) |
| AI | Claude API (claude-sonnet-4-6) |
| Database | PostgreSQL |
| Forecasts | Open-Meteo API (free, global) |

## Local setup

**Prerequisites**: Python 3.12, Node 18+, PostgreSQL 16

### 1. Database

```bash
createdb powderseek
psql powderseek -f db/schema.sql
psql powderseek -f db/seed_resorts.sql
```

### 2. Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

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
│   ├── main.py        — FastAPI routes, lifespan scheduler
│   ├── agent.py       — Claude agentic loop, tool definitions, SSE streaming
│   ├── routing.py     — Trip tier classification, resort scoring, prompt builder
│   ├── db.py          — asyncpg pool, query helpers
│   ├── forecast.py    — Open-Meteo client, background refresh
│   └── models.py      — Pydantic schemas
├── db/
│   ├── schema.sql     — 6 tables: resorts, forecasts, profiles, conversations, trips
│   └── seed_resorts.sql — 25 resorts + flight routes from SNA/LAX
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatWindow.tsx
│       │   ├── Message.tsx
│       │   ├── ChatInput.tsx
│       │   └── TripInput.tsx
│       └── hooks/
│           └── useChat.ts  — SSE streaming hook
├── PRD.md
└── ARCHITECTURE.md
```

## Resort coverage

| Tier | Duration | Regions |
|---|---|---|
| Day trip | 1 day | SoCal (Big Bear, Baldy, Snow Summit) |
| Weekend | 2–3 days | + Mammoth, June Mountain |
| Short | 4–5 days | + Utah (Alta, Snowbird, Park City, Deer Valley) |
| Medium | 6–7 days | + Colorado (Breckenridge, Telluride, Aspen), Tahoe, Canada |
| Long | 8–14 days | + Japan (Niseko, Hakuba), Europe (Chamonix, Verbier, Zermatt, Val d'Isère) |
| Expedition | 15+ days | + New Zealand (Queenstown, Mt. Hutt), Chile (Portillo, Valle Nevado) |
