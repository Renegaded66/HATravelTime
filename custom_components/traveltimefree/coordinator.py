"""Data update coordinator for the Travel Time integration."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import AddonError, TravelTimeResult, async_fetch_travel_time
from .const import CONF_END, CONF_SCAN_INTERVAL, CONF_START, DEFAULT_SCAN_INTERVAL, DOMAIN
from .location import LocationError, ResolvedLocation, resolve_location

_LOGGER = logging.getLogger(__name__)


class TravelTimeCoordinator(DataUpdateCoordinator[TravelTimeResult]):
    """Fetch the travel time of one trip.

    The start and destination are resolved on every update, so a ``person`` or
    ``device_tracker`` is evaluated with the coordinates it has **at request time**.
    """

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator from the config entry."""
        self.entry = entry
        self.config: dict[str, Any] = {**entry.data, **entry.options}
        self.last_update: datetime | None = None
        self.last_error: str | None = None
        self.start: ResolvedLocation | None = None
        self.end: ResolvedLocation | None = None

        interval = self._scan_interval()
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {self.trip_name}",
            update_interval=timedelta(minutes=interval) if interval else None,
        )

    def _scan_interval(self) -> int:
        """Return the configured update interval in minutes (0 = manual only)."""
        try:
            return max(0, int(self.config.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL))
        except (TypeError, ValueError):
            return DEFAULT_SCAN_INTERVAL

    async def _async_update_data(self) -> TravelTimeResult:
        """Resolve both endpoints and ask the add-on for the current travel time."""
        start = self._resolve(CONF_START)
        end = self._resolve(CONF_END)

        session = async_get_clientsession(self.hass)
        try:
            result = await async_fetch_travel_time(session, start.query, end.query)
        except AddonError as err:
            self.last_error = str(err)
            raise UpdateFailed(str(err)) from err

        self.start = start
        self.end = end
        self.last_error = None
        self.last_update = dt_util.utcnow()
        _LOGGER.debug(
            "Reisezeit %s -> %s: %s min", start.label, end.label, result.minutes
        )
        return result

    def _resolve(self, key: str) -> ResolvedLocation:
        """Resolve one endpoint, turning configuration problems into UpdateFailed."""
        value = self.config.get(key) or ""
        try:
            return resolve_location(value, self.hass.states)
        except LocationError as err:
            self.last_error = str(err)
            raise UpdateFailed(str(err)) from err

    @property
    def trip_name(self) -> str:
        """Return the configured trip name."""
        return self.config.get(CONF_NAME) or self.entry.title
