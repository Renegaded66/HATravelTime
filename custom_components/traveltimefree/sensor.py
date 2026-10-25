"""Sensors for the Travel Time integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TravelTimeCoordinator

# Version 1 used "<entry_id>_<index>" / "<entry_id>_<index>_last_update" as unique ids.
# One trip per entry means index 0 - keeping the ids stable preserves entity ids,
# history and dashboards for existing installations.
ENTITY_KEY = "0"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[TravelTimeCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors of one trip."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            TravelTimeSensor(coordinator, entry.entry_id),
            TravelTimeLastUpdateSensor(coordinator, entry.entry_id),
        ]
    )


class TravelTimeBaseSensor(CoordinatorEntity[TravelTimeCoordinator], SensorEntity):
    """Common device info for all entities of a trip."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: TravelTimeCoordinator, entry_id: str) -> None:
        """Initialise the sensor base."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=coordinator.trip_name,
            manufacturer="Google Maps (scraping)",
            model="Reisezeit",
            configuration_url="https://github.com/Renegaded66/HATravelTime",
        )


class TravelTimeSensor(TravelTimeBaseSensor):
    """Current travel time in minutes."""

    _attr_translation_key = "travel_time"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_attribution = "Daten von Google Maps"

    def __init__(self, coordinator: TravelTimeCoordinator, entry_id: str) -> None:
        """Initialise the travel time sensor."""
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_{ENTITY_KEY}"

    @property
    def native_value(self) -> float | None:
        """Return the travel time in minutes."""
        return self.coordinator.data.minutes if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the endpoints that were actually used for the last request."""
        attributes: dict[str, Any] = {
            "start": self.coordinator.config.get("start"),
            "end": self.coordinator.config.get("end"),
        }
        if (start := self.coordinator.start) is not None:
            attributes["start_query"] = start.query
            attributes["start_source"] = start.source
            attributes["start_label"] = start.label
        if (end := self.coordinator.end) is not None:
            attributes["end_query"] = end.query
            attributes["end_source"] = end.source
            attributes["end_label"] = end.label
        if self.coordinator.data and self.coordinator.data.distance_km is not None:
            attributes["distance_km"] = self.coordinator.data.distance_km
        if (last_update := self.coordinator.last_update) is not None:
            attributes["last_successful_update"] = last_update.isoformat()
        return attributes


class TravelTimeLastUpdateSensor(TravelTimeBaseSensor):
    """Timestamp of the last successful request."""

    _attr_translation_key = "last_updated"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: TravelTimeCoordinator, entry_id: str) -> None:
        """Initialise the timestamp sensor."""
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_{ENTITY_KEY}_last_update"

    @property
    def native_value(self) -> datetime | None:
        """Return the time of the last successful request."""
        return self.coordinator.last_update
