"""Tests for the entity metadata (unique ids, device info, values)."""

from __future__ import annotations

from dataclasses import dataclass

import _ha_stub_entities

_ha_stub_entities.install()

from _loader import load  # noqa: E402

load("api")
load("location")
coordinator_module = load("coordinator")
sensor_module = load("sensor")
button_module = load("button")

TravelTimeCoordinator = coordinator_module.TravelTimeCoordinator
TravelTimeSensor = sensor_module.TravelTimeSensor
TravelTimeLastUpdateSensor = sensor_module.TravelTimeLastUpdateSensor
TravelTimeButton = button_module.TravelTimeButton
TravelTimeResult = load("api").TravelTimeResult


class FakeEntry:
    def __init__(self) -> None:
        self.entry_id = "abc123"
        self.title = "Arbeitsweg"
        self.data = {"name": "Arbeitsweg", "start": "person.devon", "end": "zone.arbeit"}
        self.options = {}


def make_coordinator(interval: int | None = None) -> TravelTimeCoordinator:
    entry = FakeEntry()
    if interval is not None:
        entry.data["scan_interval"] = interval
    coordinator = TravelTimeCoordinator(hass=None, entry=entry)
    coordinator.data = TravelTimeResult(minutes=16.0, distance_km=12.4)
    coordinator.start = load("location").ResolvedLocation(
        query="51.500000,7.400000",
        source="entity",
        label="Devon (person.devon)",
        entity_id="person.devon",
        latitude=51.5,
        longitude=7.4,
    )
    coordinator.end = load("location").ResolvedLocation(
        query="51.600000,7.500000",
        source="entity",
        label="Arbeit (zone.arbeit)",
        entity_id="zone.arbeit",
        latitude=51.6,
        longitude=7.5,
    )
    return coordinator


def test_travel_time_sensor_keeps_the_historic_unique_id():
    """Version 1 used "<entry_id>_0" - changing it would orphan existing history."""
    sensor = TravelTimeSensor(make_coordinator(), "abc123")

    assert sensor._attr_unique_id == "abc123_0"


def test_last_update_sensor_keeps_the_historic_unique_id():
    sensor = TravelTimeLastUpdateSensor(make_coordinator(), "abc123")

    assert sensor._attr_unique_id == "abc123_0_last_update"


def test_button_keeps_the_historic_unique_id():
    button = TravelTimeButton(make_coordinator(), "abc123")

    assert button._attr_unique_id == "abc123_0_button"


def test_travel_time_value_and_unit():
    sensor = TravelTimeSensor(make_coordinator(), "abc123")

    assert sensor.native_value == 16.0
    assert sensor._attr_native_unit_of_measurement == "min"
    assert sensor._attr_device_class == "duration"
    assert sensor._attr_state_class == "measurement"


def test_value_is_none_without_data():
    coordinator = make_coordinator()
    coordinator.data = None

    assert TravelTimeSensor(coordinator, "abc123").native_value is None


def test_attributes_describe_the_endpoints_that_were_used():
    sensor = TravelTimeSensor(make_coordinator(), "abc123")

    attributes = sensor.extra_state_attributes

    assert attributes["start"] == "person.devon"
    assert attributes["start_query"] == "51.500000,7.400000"
    assert attributes["start_source"] == "entity"
    assert attributes["start_label"] == "Devon (person.devon)"
    assert attributes["distance_km"] == 12.4


def test_entities_share_one_device_per_trip():
    coordinator = make_coordinator()
    sensor = TravelTimeSensor(coordinator, "abc123")
    button = TravelTimeButton(coordinator, "abc123")

    assert sensor._attr_device_info["identifiers"] == {("traveltime", "abc123")}
    assert sensor._attr_device_info["name"] == "Arbeitsweg"
    assert button._attr_device_info["identifiers"] == {("traveltime", "abc123")}


def test_trip_name_follows_the_options():
    coordinator = make_coordinator()
    coordinator.config["name"] = "Neuer Name"

    assert coordinator.trip_name == "Neuer Name"


def test_interval_zero_means_manual_only():
    coordinator = make_coordinator(interval=0)

    assert coordinator.kwargs["update_interval"] is None


def test_interval_is_applied_as_timedelta():
    coordinator = make_coordinator(interval=15)

    assert coordinator.kwargs["update_interval"].total_seconds() == 15 * 60
