from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import AsyncGenerator, Optional


def _json_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def dumps(obj) -> str:
    return json.dumps(obj, default=_json_default)

import anthropic

import db
from routing import TripContext, rank_resorts, build_agent_prompt

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048

# ---------------------------------------------------------------------------
# Tool definitions (passed to Claude)
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    {
        "name": "get_forecast",
        "description": (
            "Get the latest snow forecast for a specific resort. "
            "Use this when you need fresher or more detailed forecast data "
            "than what was provided in the initial context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "resort_id": {"type": "integer", "description": "The resort's database ID"},
            },
            "required": ["resort_id"],
        },
    },
    {
        "name": "get_resort_details",
        "description": (
            "Get full details for a resort by its slug, including terrain description, "
            "vibe tags, pass affiliations, and agent notes. "
            "Use this to answer follow-up questions about a specific resort."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "The resort slug, e.g. 'niseko' or 'alta'"},
            },
            "required": ["slug"],
        },
    },
    {
        "name": "compare_resorts",
        "description": (
            "Get side-by-side forecast and metadata for a list of resorts. "
            "Use this when the user asks to compare specific resorts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "slugs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of resort slugs to compare",
                },
            },
            "required": ["slugs"],
        },
    },
    {
        "name": "save_preference",
        "description": (
            "Persist a user preference to their profile. "
            "Call this when the user states a preference (skill level, budget, terrain, home airport, etc.) "
            "so it's remembered in future conversations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "enum": ["skill_level", "budget_level", "preferred_terrain",
                             "home_airport", "passport_countries", "max_drive_hours"],
                },
                "value": {
                    "description": "The value to save. Lists should be arrays.",
                },
            },
            "required": ["key", "value"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

_SKILL_MAP = {
    "beginner": "beginner", "novice": "beginner", "new": "beginner", "learning": "beginner",
    "intermediate": "intermediate", "mid": "intermediate", "medium": "intermediate",
    "advanced": "advanced", "experienced": "advanced", "strong": "advanced", "expert": "expert",
    "pro": "expert", "professional": "expert", "elite": "expert",
}

_BUDGET_MAP = {
    "budget": "budget", "cheap": "budget", "low": "budget", "affordable": "budget",
    "mid": "mid", "moderate": "mid", "middle": "mid", "medium": "mid",
    "premium": "premium", "high": "premium", "upper": "premium",
    "luxury": "luxury", "ultra": "luxury", "high-end": "luxury",
}


def _normalize_skill_level(value: str) -> str:
    return _SKILL_MAP.get(str(value).lower().strip(), "intermediate")


def _normalize_budget_level(value: str) -> str:
    return _BUDGET_MAP.get(str(value).lower().strip(), "mid")


async def execute_tool(name: str, inputs: dict, session_id: str) -> str:
    if name == "get_forecast":
        resort_id = inputs["resort_id"]
        resort = await db.get_resort_by_id(resort_id)
        row = await db.get_latest_forecast(resort_id)
        if not row:
            return "No forecast data available for this resort yet."
        return dumps({
            "resort_name": resort["name"] if resort else f"Resort {resort_id}",
            "resort_id": resort_id,
            "forecast_date": row["forecast_date"],
            "new_snow_cm": row["new_snow_cm"],
            "cumulative_7d_cm": row["cumulative_7d_cm"],
            "base_depth_cm": row["base_depth_cm"],
            "temperature_c": row["temperature_c"],
            "wind_kph": row["wind_kph"],
        })

    elif name == "get_resort_details":
        slug = inputs["slug"]
        row = await db.get_resort_by_slug(slug)
        if not row:
            return f"Resort '{slug}' not found."
        return dumps({
            "name": row["name"],
            "country": row["country"],
            "region": row["region"],
            "elevation_base_m": row["elevation_base_m"],
            "elevation_summit_m": row["elevation_summit_m"],
            "vertical_drop_m": row["vertical_drop_m"],
            "terrain_tags": list(row["terrain_tags"]),
            "vibe_tags": list(row["vibe_tags"]),
            "budget_tier": row["budget_tier"],
            "pass_affiliations": list(row["pass_affiliations"]),
            "avg_annual_snowfall_cm": row["avg_annual_snowfall_cm"],
            "season": f"month {row['season_start_month']} – month {row['season_end_month']}",
            "notes": row["agent_notes"],
        })

    elif name == "compare_resorts":
        slugs = inputs["slugs"]
        results = []
        for slug in slugs:
            resort = await db.get_resort_by_slug(slug)
            if not resort:
                continue
            forecast = await db.get_latest_forecast(resort["id"])
            results.append({
                "name": resort["name"],
                "slug": slug,
                "budget_tier": resort["budget_tier"],
                "terrain_tags": list(resort["terrain_tags"]),
                "new_snow_cm": forecast["new_snow_cm"] if forecast else None,
                "cumulative_7d_cm": forecast["cumulative_7d_cm"] if forecast else None,
                "base_depth_cm": forecast["base_depth_cm"] if forecast else None,
                "notes": resort["agent_notes"],
            })
        return dumps(results)

    elif name == "save_preference":
        key = inputs["key"]
        value = inputs["value"]

        if key == "skill_level":
            value = _normalize_skill_level(value)
        elif key == "budget_level":
            value = _normalize_budget_level(value)

        await db.upsert_user_profile(session_id, {key: value})
        return f"Saved: {key} = {value}"

    return f"Unknown tool: {name}"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_BASE = """You are Powderseek, an AI ski and snowboard trip planner.
Your job is to recommend the best destination based on live snow forecasts,
travel time, the user's skill level, terrain preference, and budget.

Guidelines:
- Be direct and confident. The user wants a recommendation, not a list of options.
- Lead with your top pick and explain why — snow quality, travel tradeoff, experience.
- For long trips (7+ days), sell the experience: culture, food, terrain character.
- Be honest about weak forecasts. If the snow is flat everywhere, say so and suggest timing.
- Use the save_preference tool proactively when the user mentions skill level, budget, or preferences.
- Keep responses conversational. No bullet-point walls.
- ALWAYS refer to resorts by their full name (e.g. "Niseko United", "Mammoth Mountain"). Never say "Resort #3" or use numeric IDs in your response.
"""



# ---------------------------------------------------------------------------
# Agentic streaming loop
# ---------------------------------------------------------------------------

async def run_agent(
    session_id: str,
    user_message: str,
    trip_ctx: Optional[TripContext],
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields text chunks (SSE-ready).
    Handles multi-turn tool calls internally before yielding continuation text.
    """
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build ranked resort context if we have trip info; otherwise reload last session context
    ranked = []
    if trip_ctx:
        resorts = await db.get_resorts_with_forecasts()
        flight_table = await db.get_flight_table(trip_ctx.origin_airport)
        ranked = rank_resorts(resorts, trip_ctx, flight_table, top_n=6)
        resort_context = build_agent_prompt(ranked, trip_ctx)
        await db.save_session_resort_context(session_id, resort_context)
        system_prompt = f"{SYSTEM_BASE}\n\n{resort_context}"
    else:
        resort_context = await db.get_session_resort_context(session_id)
        system_prompt = f"{SYSTEM_BASE}\n\n{resort_context}" if resort_context else SYSTEM_BASE

    # Load conversation history and append current message
    history = await db.get_conversation_history(session_id)
    messages = history + [{"role": "user", "content": user_message}]

    full_response = ""

    # Agentic loop: keep going until no more tool calls
    while True:
        tool_calls: list[dict] = []
        assistant_content = []
        current_tool: Optional[dict] = None

        async with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
            tools=TOOLS,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool = {"id": block.id, "name": block.name, "input_str": ""}
                    elif block.type == "text":
                        current_tool = None

                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        yield delta.text
                        full_response += delta.text
                    elif delta.type == "input_json_delta" and current_tool:
                        current_tool["input_str"] += delta.partial_json

                elif event.type == "content_block_stop":
                    if current_tool:
                        tool_calls.append(current_tool)
                        current_tool = None

            final = await stream.get_final_message()
            assistant_content = final.content
            stop_reason = final.stop_reason

        if stop_reason != "tool_use" or not tool_calls:
            break

        # Execute tools and build tool_result message
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        for tc in tool_calls:
            try:
                tool_input = json.loads(tc["input_str"]) if tc["input_str"] else {}
            except json.JSONDecodeError:
                tool_input = {}

            result = await execute_tool(tc["name"], tool_input, session_id)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc["id"],
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

    # Persist the exchange
    await db.save_message(session_id, "user", user_message)
    await db.save_message(session_id, "assistant", full_response)
