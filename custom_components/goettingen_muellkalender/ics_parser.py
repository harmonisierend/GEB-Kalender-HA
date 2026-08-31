"""Parsing helpers for the GEB waste collection calendar export.

GEB Göttingen offers the calendar as an ICS (iCalendar 2.0) or legacy
vCalendar (1.0) export. Both formats use ``BEGIN:VEVENT`` blocks with a
``DTSTART`` and ``SUMMARY``. We first try a proper parse with
``icalendar``/``recurring_ical_events`` (handles recurrence rules and
timezones correctly) and fall back to a small regex-based parser for
payloads the library can't handle, since GEB's export historically used
one flat event per date rather than recurrence rules.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

_LOGGER = logging.getLogger(__name__)

_VEVENT_RE = re.compile(r"BEGIN:VEVENT(.*?)END:VEVENT", re.DOTALL)
_DTSTART_RE = re.compile(r"DTSTART[^:\r\n]*:(\d{8})")
_SUMMARY_RE = re.compile(r"SUMMARY[^:\r\n]*:(.+)")


def parse_calendar(
    raw_text: str, lookback_days: int, lookahead_days: int
) -> dict[str, list[date]]:
    """Parse an ICS/vCalendar payload into {summary: [dates]}."""
    events = _parse_with_icalendar(raw_text, lookback_days, lookahead_days)
    if not events and "BEGIN:VEVENT" in raw_text:
        _LOGGER.debug("Falling back to regex based calendar parsing")
        events = _parse_with_regex(raw_text)
    return events


def _parse_with_icalendar(
    raw_text: str, lookback_days: int, lookahead_days: int
) -> dict[str, list[date]]:
    try:
        import icalendar
        import recurring_ical_events
    except ImportError:
        return {}

    try:
        calendar = icalendar.Calendar.from_ical(raw_text)
    except Exception as err:  # noqa: BLE001 - library raises various errors
        _LOGGER.debug("icalendar could not parse calendar: %s", err)
        return {}

    start = datetime.now() - timedelta(days=lookback_days)
    end = datetime.now() + timedelta(days=lookahead_days)

    try:
        occurrences = recurring_ical_events.of(calendar).between(start, end)
    except Exception as err:  # noqa: BLE001 - library raises various errors
        _LOGGER.debug("recurring_ical_events failed to expand calendar: %s", err)
        return {}

    events: dict[str, list[date]] = {}
    for component in occurrences:
        summary = str(component.get("SUMMARY", "")).strip()
        if not summary:
            continue
        dtstart = component.get("DTSTART")
        if dtstart is None:
            continue
        value = dtstart.dt
        event_date = value.date() if isinstance(value, datetime) else value
        events.setdefault(summary, []).append(event_date)

    return events


def _parse_with_regex(raw_text: str) -> dict[str, list[date]]:
    events: dict[str, list[date]] = {}
    for block in _VEVENT_RE.findall(raw_text):
        dt_match = _DTSTART_RE.search(block)
        summary_match = _SUMMARY_RE.search(block)
        if not dt_match or not summary_match:
            continue
        try:
            event_date = datetime.strptime(dt_match.group(1), "%Y%m%d").date()
        except ValueError:
            continue
        summary = summary_match.group(1).strip()
        events.setdefault(summary, []).append(event_date)
    return events
