"""Diagnostics for the Travel Time integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import ADDON_URL, CONF_END, CONF_SCAN_INTERVAL, CONF_START
from .coordinator import TravelTimeCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry[TravelTimeCoordinator]
) -> dict[str, Any]:
    """Return everything needed to debug a broken setup."""
    coordinator: TravelTimeCoordinator | None = getattr(entry, "runtime_data", None)
    if coordinator is None:
        return {
            "entry": {"title": entry.title, "version": entry.version},
            "error": "Der Eintrag ist nicht geladen - siehe Log und Reparaturhinweise.",
        }
    data = coordinator.data

    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "configuration": {
            "start": entry.options.get(CONF_START, entry.data.get(CONF_START)),
            "end": entry.options.get(CONF_END, entry.data.get(CONF_END)),
            "scan_interval_minutes": entry.options.get(
                CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 0)
            ),
            "addon_url": ADDON_URL,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_error": coordinator.last_error,
            "last_update": (
                coordinator.last_update.isoformat()
                if coordinator.last_update is not None
                else None
            ),
            "resolved_start": vars(coordinator.start) if coordinator.start else None,
            "resolved_end": vars(coordinator.end) if coordinator.end else None,
            "data": vars(data) if data is not None else None,
        },
    }
