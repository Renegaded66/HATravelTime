import logging
import requests

_LOGGER = logging.getLogger(__name__)

ADDON_URL = "http://localhost:5000/reisezeit"  
# Wenn dein Addon in Docker läuft, evtl. URL anpassen:
# z.B. "http://a0d7b954-reisezeit:5000/reisezeit"

def berechne_reisezeit(start: str, end: str) -> float:
    try:
        response = requests.post(
            ADDON_URL,
            json={"start": start, "end": end},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "fahrtzeit" in data:
            return data["fahrtzeit"]
        else:
            _LOGGER.error("Fehlerhafte Antwort vom Addon: %s", data)
            return -1

    except Exception as e:
        _LOGGER.error("Fehler bei Anfrage an Addon: %s", e)
        return -1
