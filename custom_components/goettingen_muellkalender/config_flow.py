"""Config flow for the Göttinger Müllkalender integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_HOUSE_NUMBER,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_STREET,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    LOOKAHEAD_DAYS,
    LOOKBACK_DAYS,
)
from .coordinator import async_fetch_calendar_text
from .ics_parser import parse_calendar

_LOGGER = logging.getLogger(__name__)


class GoettingenWasteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the GEB Göttingen waste calendar."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            street = user_input[CONF_STREET].strip()
            house_number = user_input[CONF_HOUSE_NUMBER].strip()
            name = user_input.get(CONF_NAME, "").strip() or DEFAULT_NAME

            self._async_abort_entries_match(
                {CONF_STREET: street, CONF_HOUSE_NUMBER: house_number}
            )

            try:
                raw_text = await async_fetch_calendar_text(
                    self.hass, street, house_number, date.today().year
                )
                events = parse_calendar(raw_text, LOOKBACK_DAYS, LOOKAHEAD_DAYS)
            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except aiohttp.ClientError as err:
                _LOGGER.debug("Could not fetch calendar for %s %s: %s", street, house_number, err)
                errors["base"] = "cannot_connect"
            else:
                if not events:
                    errors["base"] = "no_events"
                else:
                    return self.async_create_entry(
                        title=name,
                        data={CONF_STREET: street, CONF_HOUSE_NUMBER: house_number},
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_STREET): str,
                vol.Required(CONF_HOUSE_NUMBER): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return GoettingenWasteOptionsFlow(config_entry)


class GoettingenWasteOptionsFlow(OptionsFlow):
    """Allow the scan interval to be adjusted after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self._entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=72)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
