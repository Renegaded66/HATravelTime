"""Client for the companion Travel Time add-on.

The add-on scrapes Google Maps with Playwright and answers
``GET /traveltime?start=<...>&end=<...>`` with::

    {"travel_time_minutes": 16, "distance_km": 12.4, ...}

Older add-on versions only return ``travel_time_minutes``; everything else is optional so
that integration and add-on can be updated independently.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

import aiohttp

from .const import ADDON_PROBE_TIMEOUT, ADDON_REQUEST_TIMEOUT, ADDON_URL

_LOGGER = logging.getLogger(__name__)


class AddonError(Exception):
    """Base error for the companion add-on."""


class AddonConnectionError(AddonError):
    """The add-on could not be reached."""


class AddonResponseError(AddonError):
    """The add-on answered but could not deliver a travel time."""


@dataclass(frozen=True)
class TravelTimeResult:
    """One successful travel time request."""

    minutes: float
    distance_km: float | None = None
    distance_text: str | None = None


def parse_payload(payload: Any) -> TravelTimeResult:
    """Validate an add-on response.

    Kept free of Home Assistant imports so it can be unit tested.
    """
    if not isinstance(payload, dict):
        raise AddonResponseError(f"Unerwartete Antwort des Add-ons: {payload!r}")

    if error := payload.get("error"):
        raise AddonResponseError(str(error))

    raw_minutes = payload.get("travel_time_minutes")
    if raw_minutes is None:
        raise AddonResponseError("Antwort des Add-ons enthält keine Reisezeit")

    try:
        minutes = float(raw_minutes)
    except (TypeError, ValueError) as err:
        raise AddonResponseError(
            f"Ungültige Reisezeit in der Antwort des Add-ons: {raw_minutes!r}"
        ) from err

    if minutes < 0:
        raise AddonResponseError("Das Add-on konnte keine Route berechnen")

    distance_km: float | None = None
    if (raw_distance := payload.get("distance_km")) is not None:
        try:
            distance_km = float(raw_distance)
        except (TypeError, ValueError):
            distance_km = None

    return TravelTimeResult(
        minutes=minutes,
        distance_km=distance_km,
        distance_text=payload.get("distance_text"),
    )


async def async_fetch_travel_time(
    session: aiohttp.ClientSession, start: str, end: str
) -> TravelTimeResult:
    """Ask the add-on for the travel time between two Google Maps queries."""
    try:
        async with asyncio.timeout(ADDON_REQUEST_TIMEOUT):
            response = await session.get(
                f"{ADDON_URL}/traveltime", params={"start": start, "end": end}
            )
            async with response:
                if response.status != 200:
                    body = (await response.text())[:300]
                    raise AddonResponseError(
                        f"Add-on antwortete mit HTTP {response.status}: {body}"
                    )
                payload = await response.json(content_type=None)
    except TimeoutError as err:
        raise AddonError(
            f"Zeitüberschreitung nach {ADDON_REQUEST_TIMEOUT} s - "
            "das Add-on hat nicht rechtzeitig geantwortet"
        ) from err
    except aiohttp.ClientError as err:
        raise AddonConnectionError(f"Add-on nicht erreichbar: {err}") from err

    return parse_payload(payload)


async def async_probe_addon(session: aiohttp.ClientSession) -> bool:
    """Return True if *anything* answers on the add-on port.

    Any HTTP status counts as reachable (older add-on versions answer 404 for /health),
    because the config flow only wants to know whether the container is up.
    """
    try:
        async with asyncio.timeout(ADDON_PROBE_TIMEOUT):
            async with session.get(f"{ADDON_URL}/health") as response:
                _LOGGER.debug("Add-on probe answered HTTP %s", response.status)
                return True
    except (TimeoutError, aiohttp.ClientError) as err:
        _LOGGER.debug("Add-on probe failed: %s", err)
        return False
