import logging
import requests

_LOGGER = logging.getLogger(__name__)

ADDON_URL = "http://127.0.0.1:6730/traveltime" # interner Name = slug des Add-ons

def berechne_reisezeit(start: str, end: str) -> float:
    """
    Fragt die Reisezeit vom Travel-Time-Add-on ab.
    """
    try:
        params = {"start": start, "end": end}
        response = requests.get(ADDON_URL, params=params, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if "travel_time_minutes" in data:
                return int(data["travel_time_minutes"])
            else:
                _LOGGER.error(f"Add-on-Fehler: {data}")
                return -1
        else:
            _LOGGER.error(f"HTTP {response.status_code}: {response.text}")
            return -1

    except Exception as e:
        _LOGGER.exception(f"Fehler beim Kontaktieren des Add-ons: {e}")
        return -1
