"""Tests for the address/entity resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from _loader import load

location = load("location")
const = load("const")

resolve_location = location.resolve_location
ResolvedLocation = location.ResolvedLocation
LocationError = location.LocationError
UnknownEntityError = location.UnknownEntityError
MissingCoordinatesError = location.MissingCoordinatesError
location_options = location.location_options
format_coordinates = location.format_coordinates


@dataclass
class FakeState:
    """Minimal stand-in for homeassistant.core.State."""

    entity_id: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)


class FakeStates:
    """Minimal stand-in for homeassistant.core.StateMachine."""

    def __init__(self, *states: FakeState) -> None:
        self._states = {state.entity_id: state for state in states}

    def get(self, entity_id: str) -> FakeState | None:
        return self._states.get(entity_id)

    def __iter__(self):
        return iter(self._states.values())


def test_address_is_passed_through_unchanged():
    result = resolve_location("Bahnhofstraße 1, 44532 Lünen", FakeStates())

    assert isinstance(result, ResolvedLocation)
    assert result.query == "Bahnhofstraße 1, 44532 Lünen"
    assert result.source == "address"
    assert result.entity_id is None
    assert result.label == "Bahnhofstraße 1, 44532 Lünen"


def test_address_is_stripped():
    assert resolve_location("  Lünen  ", FakeStates()).query == "Lünen"


def test_person_is_resolved_to_coordinates():
    states = FakeStates(
        FakeState("person.devon", "Devon", {"latitude": 51.5959933, "longitude": 7.4579821})
    )

    result = resolve_location("person.devon", states)

    assert result.source == "entity"
    assert result.query == "51.595993,7.457982"
    assert result.entity_id == "person.devon"
    assert result.label == "Devon (person.devon)"
    assert (result.latitude, result.longitude) == (51.5959933, 7.4579821)


def test_zone_and_device_tracker_are_resolved():
    states = FakeStates(
        FakeState("zone.arbeit", "Arbeit", {"latitude": 51.6, "longitude": 7.5}),
        FakeState("device_tracker.handy", "Handy", {"latitude": 51.1, "longitude": 7.2}),
    )

    assert resolve_location("zone.arbeit", states).query == "51.600000,7.500000"
    assert resolve_location("device_tracker.handy", states).query == "51.100000,7.200000"


def test_sensor_with_coordinates_is_resolved():
    states = FakeStates(
        FakeState("sensor.auto", "Auto", {"latitude": "52.5", "longitude": "13.4"})
    )

    assert resolve_location("sensor.auto", states).query == "52.500000,13.400000"


def test_coordinates_are_read_again_on_every_call():
    """A moving person must not be cached: this is what "live" resolution means."""
    states = FakeStates(
        FakeState("person.devon", "Devon", {"latitude": 51.0, "longitude": 7.0})
    )
    first = resolve_location("person.devon", states)

    states.get("person.devon").attributes["latitude"] = 52.0
    states.get("person.devon").attributes["longitude"] = 8.0
    second = resolve_location("person.devon", states)

    assert first.query == "51.000000,7.000000"
    assert second.query == "52.000000,8.000000"


def test_unknown_entity_raises():
    with pytest.raises(UnknownEntityError) as err:
        resolve_location("person.gibtsnicht", FakeStates())

    assert err.value.entity_id == "person.gibtsnicht"


def test_entity_without_coordinates_raises():
    states = FakeStates(FakeState("person.devon", "Devon", {"latitude": None, "longitude": None}))

    with pytest.raises(MissingCoordinatesError):
        resolve_location("person.devon", states)


def test_entity_with_only_latitude_raises():
    states = FakeStates(FakeState("person.devon", "Devon", {"latitude": 51.5}))

    with pytest.raises(MissingCoordinatesError):
        resolve_location("person.devon", states)


def test_entity_with_out_of_range_coordinates_raises():
    states = FakeStates(FakeState("person.devon", "Devon", {"latitude": 151.5, "longitude": 7.4}))

    with pytest.raises(MissingCoordinatesError):
        resolve_location("person.devon", states)


@pytest.mark.parametrize("value", ["", "   ", None])
def test_empty_input_raises(value):
    with pytest.raises(LocationError):
        resolve_location(value, FakeStates())


def test_text_with_dot_but_not_an_entity_id_is_an_address():
    """'Hauptstr. 5' must not be mistaken for an entity id."""
    assert resolve_location("Hauptstr. 5, Lünen", FakeStates()).source == "address"


def test_format_coordinates():
    assert format_coordinates(51.5, 7.25) == "51.500000,7.250000"


def test_location_options_only_contains_usable_entities():
    states = FakeStates(
        FakeState("person.devon", "Devon", {"latitude": 51.5, "longitude": 7.4}),
        FakeState("zone.home", "Zuhause", {"latitude": 51.6, "longitude": 7.5}),
        FakeState("device_tracker.handy", "Handy", {"latitude": 51.7, "longitude": 7.6}),
        FakeState("sensor.temperatur", "Temperatur", {"unit_of_measurement": "°C"}),
        FakeState("light.wohnzimmer", "Wohnzimmer", {"latitude": 51.8, "longitude": 7.7}),
        FakeState("person.ohne_gps", "Ohne GPS", {}),
    )

    options = location_options(states)

    assert [option["value"] for option in options] == [
        "person.devon",
        "device_tracker.handy",
        "zone.home",
    ]
    assert options[0]["label"] == "Devon (person.devon)"


def test_location_options_are_sorted_by_label():
    states = FakeStates(
        FakeState("person.zoe", "Zoe", {"latitude": 51.5, "longitude": 7.4}),
        FakeState("person.anna", "Anna", {"latitude": 51.5, "longitude": 7.4}),
    )

    assert [option["label"] for option in location_options(states)] == [
        "Anna (person.anna)",
        "Zoe (person.zoe)",
    ]


def test_coordinate_domains_match_const():
    assert set(const.COORDINATE_DOMAINS) == {"person", "zone", "device_tracker", "sensor"}
