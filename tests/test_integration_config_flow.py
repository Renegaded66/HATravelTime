"""Tests for the config/options flow helpers.

Imports ``config_flow.py`` against the stand-in from ``_ha_stub`` so that validation,
normalisation and schema construction can be checked without Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

import _ha_stub

_ha_stub.install()

from _loader import load  # noqa: E402

load("api")
config_flow = load("config_flow")

_clean = config_flow._clean
_validate_locations = config_flow._validate_locations
_schema = config_flow._schema
_location_selector = config_flow._location_selector

CONF_NAME = "name"
CONF_START = "start"
CONF_END = "end"
CONF_SCAN_INTERVAL = "scan_interval"


@dataclass
class FakeState:
    entity_id: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)


class FakeStates:
    def __init__(self, *states: FakeState) -> None:
        self._states = {state.entity_id: state for state in states}

    def get(self, entity_id: str) -> FakeState | None:
        return self._states.get(entity_id)

    def async_all(self):
        return list(self._states.values())


class FakeHass:
    def __init__(self, *states: FakeState) -> None:
        self.states = FakeStates(*states)


def test_clean_strips_and_clamps():
    cleaned = _clean(
        {
            CONF_NAME: "  Arbeitsweg ",
            CONF_START: " person.devon ",
            CONF_END: " Berlin ",
            CONF_SCAN_INTERVAL: "9999",
        }
    )

    assert cleaned == {
        CONF_NAME: "Arbeitsweg",
        CONF_START: "person.devon",
        CONF_END: "Berlin",
        CONF_SCAN_INTERVAL: 1440,
    }


def test_clean_defaults_interval_to_zero():
    cleaned = _clean({CONF_NAME: "X", CONF_START: "A", CONF_END: "B"})

    assert cleaned[CONF_SCAN_INTERVAL] == 0


def test_clean_rejects_negative_interval():
    cleaned = _clean(
        {CONF_NAME: "X", CONF_START: "A", CONF_END: "B", CONF_SCAN_INTERVAL: -5}
    )

    assert cleaned[CONF_SCAN_INTERVAL] == 0


def test_valid_input_has_no_errors():
    hass = FakeHass(
        FakeState("person.devon", "Devon", {"latitude": 51.5, "longitude": 7.4}),
        FakeState("zone.arbeit", "Arbeit", {"latitude": 51.6, "longitude": 7.5}),
    )

    errors = _validate_locations(
        hass, {CONF_NAME: "Arbeitsweg", CONF_START: "person.devon", CONF_END: "zone.arbeit"}
    )

    assert errors == {}


def test_missing_name_is_reported_on_the_name_field():
    hass = FakeHass()

    errors = _validate_locations(hass, {CONF_NAME: "  ", CONF_START: "A", CONF_END: "B"})

    assert errors == {CONF_NAME: "name_required"}


def test_missing_location_is_reported_per_field():
    errors = _validate_locations(FakeHass(), {CONF_NAME: "X", CONF_START: "", CONF_END: "B"})

    assert errors == {CONF_START: "no_location"}


def test_unknown_entity_is_reported_on_its_field():
    errors = _validate_locations(
        FakeHass(), {CONF_NAME: "X", CONF_START: "person.gibtsnicht", CONF_END: "B"}
    )

    assert errors == {CONF_START: "entity_not_found"}


def test_entity_without_coordinates_is_reported():
    hass = FakeHass(FakeState("person.devon", "Devon", {}))

    errors = _validate_locations(
        hass, {CONF_NAME: "X", CONF_START: "person.devon", CONF_END: "B"}
    )

    assert errors == {CONF_START: "entity_no_coordinates"}


def test_address_is_accepted_without_existing_entities():
    assert _validate_locations(
        FakeHass(), {CONF_NAME: "X", CONF_START: "Lünen", CONF_END: "Berlin"}
    ) == {}


def test_schema_prefills_existing_values():
    hass = FakeHass(
        FakeState("person.devon", "Devon", {"latitude": 51.5, "longitude": 7.4})
    )
    schema = _schema(
        hass,
        {
            CONF_NAME: "Arbeitsweg",
            CONF_START: "person.devon",
            CONF_END: "zone.arbeit",
            CONF_SCAN_INTERVAL: 15,
        },
    )

    result = schema(
        {
            CONF_NAME: "Arbeitsweg",
            CONF_START: "person.devon",
            CONF_END: "zone.arbeit",
            CONF_SCAN_INTERVAL: 15,
        }
    )

    assert result[CONF_NAME] == "Arbeitsweg"
    assert result[CONF_SCAN_INTERVAL] == 15


def test_schema_renders_empty_on_first_open():
    """The first render has no stored values: every field must fall back to a default."""
    schema = _schema(FakeHass(), {})

    assert schema({}) == {
        CONF_NAME: "",
        CONF_START: "",
        CONF_END: "",
        CONF_SCAN_INTERVAL: 0,
    }


def test_schema_requires_all_three_text_fields():
    schema = _schema(FakeHass(), {})

    result = schema({CONF_NAME: "X", CONF_START: "A", CONF_END: "B"})

    assert result[CONF_NAME] == "X"
    assert result[CONF_SCAN_INTERVAL] == 0


def test_schema_rejects_non_numeric_interval():
    schema = _schema(FakeHass(), {})

    with pytest.raises(Exception):
        schema(
            {CONF_NAME: "X", CONF_START: "A", CONF_END: "B", CONF_SCAN_INTERVAL: "viel"}
        )


def test_location_selector_offers_entities_and_allows_free_text():
    hass = FakeHass(
        FakeState("person.devon", "Devon", {"latitude": 51.5, "longitude": 7.4}),
        FakeState("light.wohnzimmer", "Wohnzimmer", {}),
    )
    selector = _location_selector(hass)

    assert selector.config.options == [
        {"value": "person.devon", "label": "Devon (person.devon)"}
    ]
    assert selector.config.kwargs["custom_value"] is True
