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
    CONF_HOUSE_NUMBER,
    CONF_STREET,
    FALLBACK_ICON,
    FORWARD_URL_TEMPLATE,
    LOOKAHEAD_DAYS,
    LOOKBACK_DAYS,
    MAX_UPCOMING_DATES,
)
from .ics_parser import parse_calendar

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30

# GEB's web server rejects requests without a browser-like User-Agent
# (returns 403 Forbidden for generic HTTP client user agents).
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/calendar,text/html,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9",
}

# GEB usually publishes next year's calendar in autumn. Fetching it a
# little early keeps the sensors populated across the new-year rollover.
NEXT_YEAR_FROM_MONTH = 11


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


def categorize(summary: str) -> tuple[str, str, str]:
    """Map a calendar event summary to (slug, display name, icon)."""
    lowered = summary.lower()
    for definition in CATEGORY_DEFINITIONS:
        if any(keyword in lowered for keyword in definition["keywords"]):
            return definition["slug"], definition["name"], definition["icon"]
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_") or "termin"
    return slug, summary.strip(), FALLBACK_ICON


async def async_fetch_calendar_text(
    hass: HomeAssistant, street: str, house_number: str, year: int
) -> str:
    """Download the raw ICS payload for one street/house number/year."""
    session = async_get_clientsession(hass)
    url = FORWARD_URL_TEMPLATE.format(year=year)
    params = {"str": f"{street} ", "nr": house_number, "year": str(year)}
    async with asyncio.timeout(REQUEST_TIMEOUT):
        response = await session.get(url, params=params, headers=REQUEST_HEADERS)
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
        self.street: str = entry.data[CONF_STREET]
        self.house_number: str = entry.data[CONF_HOUSE_NUMBER]

    def _years_to_fetch(self) -> list[int]:
        today = date.today()
        years = [today.year]
        if today.month >= NEXT_YEAR_FROM_MONTH:
            years.append(today.year + 1)
        return years

    async def _async_update_data(self) -> dict[str, WasteCategory]:
        raw_events: dict[str, list[date]] = {}
        last_error: Exception | None = None

        for year in self._years_to_fetch():
            try:
                raw_text = await async_fetch_calendar_text(
                    self._hass, self.street, self.house_number, year
                )
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.debug("Fetching %s calendar for %s failed: %s", year, self.street, err)
                last_error = err
                continue

            for summary, dates in parse_calendar(raw_text, LOOKBACK_DAYS, LOOKAHEAD_DAYS).items():
                raw_events.setdefault(summary, []).extend(dates)

        if not raw_events:
            raise UpdateFailed(
                "Der Kalender konnte nicht gelesen werden oder enthält keine Termine. "
                "Prüfe Straße und Hausnummer."
                + (f" Letzter Fehler: {last_error}" if last_error else "")
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
