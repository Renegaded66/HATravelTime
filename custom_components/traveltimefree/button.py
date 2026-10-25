"""Button to refresh a trip on demand."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TravelTimeCoordinator

ENTITY_KEY = "0"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[TravelTimeCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the refresh button of one trip."""
    coordinator = entry.runtime_data
    async_add_entities([TravelTimeButton(coordinator, entry.entry_id)])


class TravelTimeButton(CoordinatorEntity[TravelTimeCoordinator], ButtonEntity):
    """Trigger an immediate request against the add-on."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"
    _attr_should_poll = False

    def __init__(self, coordinator: TravelTimeCoordinator, entry_id: str) -> None:
        """Initialise the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{ENTITY_KEY}_button"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=coordinator.trip_name,
            manufacturer="Google Maps (scraping)",
            model="Reisezeit",
            configuration_url="https://github.com/Renegaded66/HATravelTime",
        )

    async def async_press(self) -> None:
        """Request a fresh travel time."""
        await self.coordinator.async_refresh()
