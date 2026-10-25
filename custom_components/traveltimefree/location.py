"""Turn a user supplied location into a Google Maps query.

The integration accepts two kinds of input for start and destination:

* a free text address (``"Bahnhofstrasse 1, 44532 Luenen"``), forwarded to Google Maps as is
* an entity id (``person.devon``, ``zone.home``, ``device_tracker.phone``, ``sensor.car``),
  resolved to the *current* latitude/longitude **at the moment of the request**

This module intentionally has no Home Assistant imports so that the resolution logic can be
unit tested without a running Home Assistant instance.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Protocol

from .const import COORDINATE_DOMAINS

# "domain.object_id" - Home Assistant entity ids are lower case.
ENTITY_ID_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z0-9_]+$")


class LocationError(Exception):
    """Base error for an unusable location input."""

    def __init__(self, message: str, *, entity_id: str | None = None) -> None:
        super().__init__(message)
        self.entity_id = entity_id


class UnknownEntityError(LocationError):
    """The input looks like an entity id but no such entity exists."""


class MissingCoordinatesError(LocationError):
    """The entity exists but currently exposes no usable latitude/longitude."""


class StateLike(Protocol):
    """The part of ``homeassistant.core.State`` we need."""

    entity_id: str
    name: str
    attributes: Mapping[str, Any]


@dataclass(frozen=True)
class ResolvedLocation:
    """A location that can be handed to the add-on."""

    query: str
    source: str  # "address" or "entity"
    label: str
    entity_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None


def format_coordinates(latitude: float, longitude: float) -> str:
    """Format coordinates the way Google Maps expects them in a /dir/ URL."""
    return f"{latitude:.6f},{longitude:.6f}"


def coordinates_from_state(state: StateLike) -> tuple[float, float] | None:
    """Return (latitude, longitude) of a state, or None if it has none right now."""
    attributes = state.attributes or {}
    raw_latitude = attributes.get("latitude")
    raw_longitude = attributes.get("longitude")
    if raw_latitude is None or raw_longitude is None:
        return None
    try:
        latitude = float(raw_latitude)
        longitude = float(raw_longitude)
    except (TypeError, ValueError):
        return None
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None
    return latitude, longitude


def resolve_location(value: str, states: Mapping[str, StateLike]) -> ResolvedLocation:
    """Resolve a config value (address or entity id) to something Google Maps understands.

    ``states`` is anything with a ``get(entity_id) -> StateLike | None`` method;
    in Home Assistant that is ``hass.states``.
    """
    text = (value or "").strip()
    if not text:
        raise LocationError("Kein Start- oder Zielpunkt angegeben")

    if not ENTITY_ID_PATTERN.match(text):
        return ResolvedLocation(query=text, source="address", label=text)

    state = states.get(text)
    if state is None:
        raise UnknownEntityError(
            f"Die Entität {text} existiert nicht", entity_id=text
        )

    coordinates = coordinates_from_state(state)
    if coordinates is None:
        raise MissingCoordinatesError(
            f"Die Entität {text} liefert aktuell keine Koordinaten", entity_id=text
        )

    latitude, longitude = coordinates
    return ResolvedLocation(
        query=format_coordinates(latitude, longitude),
        source="entity",
        label=f"{state.name} ({text})",
        entity_id=text,
        latitude=latitude,
        longitude=longitude,
    )


def location_options(entities: Iterable[StateLike]) -> list[dict[str, str]]:
    """Build the option list for the location picker (entities that carry coordinates)."""
    options: list[dict[str, str]] = []
    for state in entities:
        domain = state.entity_id.split(".", 1)[0]
        if domain not in COORDINATE_DOMAINS:
            continue
        if coordinates_from_state(state) is None:
            continue
        options.append(
            {"value": state.entity_id, "label": f"{state.name} ({state.entity_id})"}
        )
    options.sort(key=lambda option: option["label"].casefold())
    return options
