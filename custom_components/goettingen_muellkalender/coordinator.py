"""Data update coordinator for the Göttinger Müllkalender integration."""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CATEGORY_DEFINITIONS,
    CONF_ICS_URL,
    FALLBACK_ICON,
    LOOKAHEAD_DAYS,
    LOOKBACK_DAYS,
    MAX_UPCOMING_DATES,
)
from .ics_parser import parse_calendar

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


@dataclass
class WasteCategory:
    """Upcoming pickup dates for a single waste type."""

    slug: str
    name: str
    icon: str
    dates: list[date] = field(default_factory=list)

    @property
    def next_date(self) -> date | None:
        return self.dates[0] if self.dates else None

    @property
    def upcoming(self) -> list[date]:
        return self.dates[:MAX_UPCOMING_DATES]


def normalize_calendar_url(url: str) -> str:
    """Turn a webcal:// subscription link into a plain https:// URL."""
    if url.lower().startswith("webcal://"):
        return "https://" + url[len("webcal://"):]
    return url


def categorize(summary: str) -> tuple[str, str, str]:
    """Map a calendar event summary to (slug, display name, icon)."""
    lowered = summary.lower()
    for definition in CATEGORY_DEFINITIONS:
        if any(keyword in lowered for keyword in definition["keywords"]):
            return definition["slug"], definition["name"], definition["icon"]
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_") or "termin"
    return slug, summary.strip(), FALLBACK_ICON


async def async_fetch_calendar_text(hass: HomeAssistant, url: str) -> str:
    """Download the raw ICS/vCalendar payload for the given URL."""
    session = async_get_clientsession(hass)
    fetch_url = normalize_calendar_url(url)
    async with asyncio.timeout(REQUEST_TIMEOUT):
        response = await session.get(fetch_url)
        response.raise_for_status()
        return await response.text()


class GoettingenWasteCoordinator(DataUpdateCoordinator[dict[str, WasteCategory]]):
    """Fetches and parses the GEB waste calendar on a schedule."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, update_interval: timedelta
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            update_interval=update_interval,
        )
        self._hass = hass
        self._url = entry.data[CONF_ICS_URL]

    async def _async_update_data(self) -> dict[str, WasteCategory]:
        try:
            raw_text = await async_fetch_calendar_text(self._hass, self._url)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Fehler beim Abrufen des Kalenders: {err}") from err

        raw_events = parse_calendar(raw_text, LOOKBACK_DAYS, LOOKAHEAD_DAYS)
        if not raw_events:
            raise UpdateFailed(
                "Der Kalender konnte nicht gelesen werden oder enthält keine Termine."
            )

        today = date.today()
        categories: dict[str, WasteCategory] = {}
        for summary, dates in raw_events.items():
            slug, name, icon = categorize(summary)
            future_dates = sorted({d for d in dates if d >= today})
            if not future_dates:
                continue
            if slug in categories:
                categories[slug].dates = sorted(
                    set(categories[slug].dates) | set(future_dates)
                )
            else:
                categories[slug] = WasteCategory(
                    slug=slug, name=name, icon=icon, dates=future_dates
                )

        return categories
