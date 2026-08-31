"""Sensor platform for the Göttinger Müllkalender integration."""
from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GoettingenWasteCoordinator, WasteCategory


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for every waste type found in the calendar.

    GEB's calendar can contain a different set of waste types per
    street, so sensors are created dynamically as new categories show
    up in the coordinator data instead of being hard-coded.
    """
    coordinator: GoettingenWasteCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_slugs: set[str] = set()

    @callback
    def _add_new_entities() -> None:
        new_slugs = set(coordinator.data or {}) - known_slugs
        if not new_slugs:
            return
        known_slugs.update(new_slugs)
        async_add_entities(
            WasteCategorySensor(coordinator, entry, slug) for slug in new_slugs
        )

    _add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_entities))


class WasteCategorySensor(CoordinatorEntity[GoettingenWasteCoordinator], SensorEntity):
    """Next pickup date for a single waste type (Tonne)."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: GoettingenWasteCoordinator, entry: ConfigEntry, slug: str
    ) -> None:
        super().__init__(coordinator)
        self._slug = slug
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Göttinger Entsorgungsbetriebe",
            model="Müllkalender",
        )

    @property
    def _category(self) -> WasteCategory | None:
        data = self.coordinator.data
        return data.get(self._slug) if data else None

    @property
    def available(self) -> bool:
        return super().available and self._category is not None

    @property
    def name(self) -> str | None:
        category = self._category
        return category.name if category else None

    @property
    def icon(self) -> str | None:
        category = self._category
        return category.icon if category else None

    @property
    def native_value(self) -> date | None:
        category = self._category
        return category.next_date if category else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        category = self._category
        if category is None:
            return {}
        next_date = category.next_date
        return {
            "days_remaining": (next_date - date.today()).days if next_date else None,
            "upcoming_dates": [d.isoformat() for d in category.upcoming],
        }
