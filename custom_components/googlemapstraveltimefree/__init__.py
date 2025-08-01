"""The Google Maps Travel Time Free (No Api Key) integration."""

from __future__ import annotations

#from homeassistant.components.googlemapstraveltimefree import coordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import TravelTimeCoordinator

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

# TODO Create ConfigEntry type alias with API object
type TravelTimeConfigEntry = ConfigEntry[coordinator]
# TODO Rename type alias and update all entry annotations
#type New_NameConfigEntry = ConfigEntry[MyApi]  # noqa: F821
type TravelTimeConfigEntry = ConfigEntry[TravelTimeCoordinator]

# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: TravelTimeConfigEntry) -> bool:
    """Set up Google Maps Travel Time Free (No Api Key) from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)
    coordinator = TravelTimeCoordinator(hass, entry.data)
    entry.runtime_data = coordinator
    # await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        # Nur den spezifischen Eintrag aus runtime_data entfernen
        entry.runtime_data = None  # optional, HG automatisch gelöscht
    return unload_ok
