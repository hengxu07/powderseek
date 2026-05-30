from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Optional

import anthropic
import httpx

import db

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
HTTP_TIMEOUT = 15.0
USER_AGENT = "Powderseek/1.0 (season-status worker; +https://powderseek.app)"
MAX_PAGE_CHARS = 20_000          # cap on stripped text fed to Claude
MAX_CONCURRENCY = 6              # parallel resorts; gentle on remote sites
DATE_CLAMP_MONTHS = 18           # reject open/close dates outside ±18mo from today
MIN_EVIDENCE_CHARS = 12          # below this the substring check is too weak

_TAG_RE      = re.compile(r"<[^>]+>")
_SCRIPT_RE   = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_WS_RE       = re.compile(r"\s+")

REPORT_TOOL = {
    "name": "report_season_dates",
    "description": (
        "Report the resort's current operating-season open and close dates as "
        "best determined from the page text. If the resort is currently mid-season, "
        "infer the season's start (commonly Nov/Dec of last year). If the page only "
        "discusses a future season, report that future window."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "open_date":  {"type": ["string", "null"], "description": "ISO YYYY-MM-DD, or null if not determinable"},
            "close_date": {"type": ["string", "null"], "description": "ISO YYYY-MM-DD, or null if not determinable"},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "evidence":   {"type": "string", "description": "The exact phrase or sentence from the page that supports the dates"},
        },
        "required": ["open_date", "close_date", "confidence", "evidence"],
    },
}


def _strip_html(html: str) -> str:
    """Strip tags + scripts + styles, collapse whitespace, cap length."""
    text = _SCRIPT_RE.sub(" ", html)
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text[:MAX_PAGE_CHARS]


def _date_in_window(d: date, today: date) -> bool:
    """Sanity gate: reject dates further than DATE_CLAMP_MONTHS from today.
    A resort site that claims a 2099 closing date has either been mis-parsed or
    is feeding the model an injection payload — either way, drop it."""
    lo = today - timedelta(days=DATE_CLAMP_MONTHS * 31)
    hi = today + timedelta(days=DATE_CLAMP_MONTHS * 31)
    return lo <= d <= hi


def _evidence_supported(evidence: str, page_text: str) -> bool:
    """Require the model's cited evidence to actually appear in the scraped page.
    Defends against prompt injection that steers the model into inventing both
    dates and the justification."""
    if not evidence or len(evidence) < MIN_EVIDENCE_CHARS:
        return False
    norm = lambda s: _WS_RE.sub(" ", s.lower()).strip()
    return norm(evidence) in norm(page_text)


def _parse_iso(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        logger.warning("season_status: bad date string %r", s)
        return None


async def _fetch_page(client: httpx.AsyncClient, url: str) -> Optional[str]:
    try:
        resp = await client.get(url, follow_redirects=True, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as e:
        logger.warning("season_status: fetch failed for %s — %s", url, e)
        return None


async def _ask_claude(
    anthro: anthropic.AsyncAnthropic,
    resort_name: str,
    page_text: str,
) -> Optional[dict]:
    today = date.today().isoformat()
    prompt = (
        f"Today is {today}. Below is the homepage text for {resort_name}, a ski resort. "
        f"Find the current operating season's open and close dates. The page may say "
        f"\"open through April 12\", \"closing day: April 12, 2026\", \"opens Nov 21\", "
        f"or similar. If only a month is given (no day), pick a reasonable day. "
        f"If the page only discusses a future season (e.g. \"reopening winter 2026/27\"), "
        f"report that. Use the report_season_dates tool to return your finding. "
        f"Set confidence=low if you had to guess substantially.\n\n"
        f"---PAGE TEXT---\n{page_text}"
    )
    try:
        msg = await anthro.messages.create(
            model=MODEL,
            max_tokens=512,
            tools=[REPORT_TOOL],
            tool_choice={"type": "tool", "name": "report_season_dates"},
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        logger.warning("season_status: Claude call failed for %s — %s", resort_name, e)
        return None

    for block in msg.content:
        if block.type == "tool_use" and block.name == "report_season_dates":
            return block.input  # already a dict
    logger.warning("season_status: Claude returned no tool call for %s", resort_name)
    return None


async def refresh_resort(
    http: httpx.AsyncClient,
    anthro: anthropic.AsyncAnthropic,
    resort: dict,
) -> None:
    """Fetch one resort's status page, parse via Claude, upsert dated season window."""
    name = resort["name"]
    url = resort["status_url"]

    html = await _fetch_page(http, url)
    if not html:
        return

    text = _strip_html(html)
    if not text:
        logger.warning("season_status: empty page text for %s (%s)", name, url)
        return

    parsed = await _ask_claude(anthro, name, text)
    if not parsed:
        return

    if parsed.get("confidence") == "low":
        logger.info(
            "season_status: low confidence for %s; skipping write. evidence=%r",
            name, parsed.get("evidence"),
        )
        return

    open_d  = _parse_iso(parsed.get("open_date"))
    close_d = _parse_iso(parsed.get("close_date"))
    if not (open_d and close_d):
        logger.info(
            "season_status: incomplete dates for %s (open=%s close=%s); skipping",
            name, open_d, close_d,
        )
        return

    today = date.today()
    if not (_date_in_window(open_d, today) and _date_in_window(close_d, today)):
        logger.warning(
            "season_status: dates outside ±%dmo window for %s (open=%s close=%s); "
            "possible prompt-injection or parse error — skipping",
            DATE_CLAMP_MONTHS, name, open_d, close_d,
        )
        return

    if open_d > close_d:
        logger.warning(
            "season_status: open > close for %s (open=%s close=%s); skipping",
            name, open_d, close_d,
        )
        return

    evidence = parsed.get("evidence", "")
    if not _evidence_supported(evidence, text):
        logger.warning(
            "season_status: evidence not found in page for %s; possible "
            "fabrication or injection. evidence=%r — skipping",
            name, evidence,
        )
        return

    await db.upsert_season_status(resort["id"], open_d, close_d)
    logger.info(
        "season_status: %s → open=%s close=%s (evidence=%r)",
        name, open_d, close_d, evidence,
    )


async def refresh_all_season_status() -> None:
    """Refresh dated season status for every resort with a status_url."""
    resorts = await db.get_resorts_for_status_refresh()
    if not resorts:
        logger.info("season_status: no resorts have status_url; nothing to refresh")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("season_status: ANTHROPIC_API_KEY not set; skipping refresh")
        return

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    headers = {"User-Agent": USER_AGENT}
    started = datetime.now()

    async with httpx.AsyncClient(headers=headers) as http:
        anthro = anthropic.AsyncAnthropic(api_key=api_key)

        async def bounded(r):
            async with sem:
                try:
                    await refresh_resort(http, anthro, r)
                except Exception:
                    logger.exception("season_status: unexpected error for %s", r["name"])

        await asyncio.gather(*(bounded(r) for r in resorts))

    elapsed = (datetime.now() - started).total_seconds()
    logger.info("season_status: refreshed %d resorts in %.1fs", len(resorts), elapsed)
