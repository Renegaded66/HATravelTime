from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import TravelTimeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[TravelTimeCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    buttons = []
    title = entry.title
    for idx, _ in enumerate(coordinator.config.get("coordinates", [])):
        buttons.append(TravelTimeButton(coordinator, entry.entry_id, idx, title))
    async_add_entities(buttons)


class TravelTimeButton(ButtonEntity):
    def __init__(
        self, coordinator: TravelTimeCoordinator, entry_id: str, idx: int, title: str
    ):
        self.coordinator = coordinator
        self._idx = idx
        self._attr_name = f"{title} Update Travel Time"
        self._attr_unique_id = f"{entry_id}_{idx}_button"

    async def async_press(self) -> None:
        await self.coordinator.async_refresh()
