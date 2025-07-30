import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.dt import now

from .const import DOMAIN
from .helpers import berechne_reisezeit

_LOGGER = logging.getLogger(__name__)
# SCAN_INTERVAL = timedelta(minutes=5)


class TravelTimeCoordinator(DataUpdateCoordinator[dict[int, float]]):
    def __init__(self, hass, config):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self.config = config

    async def _async_update_data(self):
        results = {}
        for idx, coords in enumerate(self.config.get("coordinates", [])):
            travel = await self.hass.async_add_executor_job(
                berechne_reisezeit,
                coords["Start"],
                coords["End"],
            )
            results[idx] = float(travel)

        # Timestamp setzen
        self.last_update = now()
        return results
