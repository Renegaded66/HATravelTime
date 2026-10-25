"""Tests for the add-on response parsing."""

from __future__ import annotations

import pytest

from _loader import load

api = load("api")

parse_payload = api.parse_payload
AddonResponseError = api.AddonResponseError


def test_parses_minimal_legacy_response():
    """Add-on 1.0.1 answers with the travel time only - must keep working."""
    result = parse_payload({"travel_time_minutes": 16})

    assert result.minutes == 16.0
    assert result.distance_km is None
    assert result.distance_text is None


def test_parses_current_response_with_distance():
    result = parse_payload(
        {
            "travel_time_minutes": 27,
            "distance_km": "12.4",
            "distance_text": "12,4 km",
            "version": "1.1.0",
        }
    )

    assert result.minutes == 27.0
    assert result.distance_km == 12.4
    assert result.distance_text == "12,4 km"


def test_error_payload_raises_with_message():
    with pytest.raises(AddonResponseError) as err:
        parse_payload({"error": "Reisezeit konnte nicht ermittelt werden."})

    assert "Reisezeit konnte nicht ermittelt werden." in str(err.value)


def test_missing_travel_time_raises():
    with pytest.raises(AddonResponseError):
        parse_payload({"distance_km": 12.4})


def test_non_numeric_travel_time_raises():
    with pytest.raises(AddonResponseError):
        parse_payload({"travel_time_minutes": "unbekannt"})


def test_negative_travel_time_raises():
    """The old add-on used -1 as "failed" marker - never show that as a value."""
    with pytest.raises(AddonResponseError):
        parse_payload({"travel_time_minutes": -1})


def test_non_dict_payload_raises():
    with pytest.raises(AddonResponseError):
        parse_payload(["16"])


def test_broken_distance_is_ignored_but_minutes_kept():
    result = parse_payload({"travel_time_minutes": 16, "distance_km": "keine Ahnung"})

    assert result.minutes == 16.0
    assert result.distance_km is None
