"""Two Sensors, one for the travel time and one for last update"""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import TravelTimeCoordinator


class TravelTimeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: coordinator, entry_id: str, idx: int, title: str):
        super().__init__(coordinator)
        self._idx = idx
        self._attr_name = f"{title} Travel Time"
        self._attr_unique_id = f"{entry_id}_{idx}"
        self._attr_native_unit_of_measurement = "min"
        self._attr_should_poll = False

    @property
    def native_value(self):
        return self.coordinator.data.get(self._idx) if self.coordinator.data else None


class TravelTimeLastUpdateSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id: str, idx: int, title: str):
        super().__init__(coordinator)
        self._idx = idx
        self._attr_name = f"{title} Last Update"
        self._attr_unique_id = f"{entry_id}_{idx}_last_update"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_should_poll = False

    @property
    def native_value(self) -> str | None:
        return self.coordinator.last_update


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[TravelTimeCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator = entry.runtime_data
    title = entry.title
    entities = []
    for idx, _ in enumerate(coordinator.config.get("coordinates", [])):
        entities.append(TravelTimeSensor(coordinator, entry.entry_id, idx, title))
        entities.append(
            TravelTimeLastUpdateSensor(coordinator, entry.entry_id, idx, title)
        )
    async_add_entities(entities)  # , update_before_add=True)
