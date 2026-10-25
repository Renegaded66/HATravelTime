"""The Travel Time integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_END, CONF_START, CONFIG_VERSION
from .coordinator import TravelTimeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

TravelTimeConfigEntry = ConfigEntry[TravelTimeCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TravelTimeConfigEntry) -> bool:
    """Set up one trip from a config entry."""
    coordinator = TravelTimeCoordinator(hass, entry)
    # Raises ConfigEntryNotReady if the add-on is down or Google Maps cannot be reached,
    # so setup problems are visible in the UI instead of silently yielding "unknown".
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TravelTimeConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate a version 1 entry (one entry with a list of coordinate pairs) to version 2."""
    if entry.version > CONFIG_VERSION:
        # Downgrade from a newer version - do not touch the entry.
        _LOGGER.error(
            "Eintrag %s hat Version %s, diese Integration kennt nur %s",
            entry.entry_id,
            entry.version,
            CONFIG_VERSION,
        )
        return False

    if entry.version == 1:
        coordinates = entry.data.get("coordinates") or []
        if not coordinates:
            _LOGGER.error(
                "Eintrag %s enthält keinen Start-/Zielpunkt und kann nicht migriert werden",
                entry.entry_id,
            )
            return False

        if len(coordinates) > 1:
            _LOGGER.warning(
                "Eintrag %s enthielt %s Strecken; es wird nur die erste übernommen. "
                "Weitere Strecken bitte als eigenen Eintrag anlegen.",
                entry.entry_id,
                len(coordinates),
            )

        first = coordinates[0]
        start = (first.get("Start") or "").strip()
        end = (first.get("End") or "").strip()
        if not start or not end:
            _LOGGER.error(
                "Eintrag %s enthält keinen gültigen Start-/Zielpunkt", entry.entry_id
            )
            return False

        name = (entry.data.get(CONF_NAME) or entry.title or "Reisezeit").strip()
        hass.config_entries.async_update_entry(
            entry,
            title=name,
            data={CONF_NAME: name, CONF_START: start, CONF_END: end},
            version=CONFIG_VERSION,
        )
        _LOGGER.info("Eintrag %s auf Version %s migriert", entry.entry_id, CONFIG_VERSION)

    return entry.version == CONFIG_VERSION
