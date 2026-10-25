"""Tests for the add-on parser and URL builder.

Run with:  pytest addon/traveltime/tests
Requires only flask (playwright is imported lazily inside get_travel_time).
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import (  # noqa: E402
    DISTANCE_PATTERN,
    DURATION_PATTERN,
    build_maps_url,
    distance_to_km,
    duration_to_minutes,
)


def test_duration_to_minutes_supports_minutes():
    assert duration_to_minutes("27 min") == 27


def test_duration_to_minutes_supports_hours_and_minutes():
    assert duration_to_minutes("2 h 31 min") == 151


def test_duration_to_minutes_returns_none_without_duration():
    assert duration_to_minutes("Route ohne Angabe") is None


def test_current_google_maps_route_card_fixture_contains_duration_and_distance():
    text = Path(__file__).with_name("google_maps_route_text.txt").read_text(encoding="utf-8")

    assert DURATION_PATTERN.search(text)
    assert DISTANCE_PATTERN.search(text)
    assert duration_to_minutes(text) == 27


def test_distance_to_km_handles_german_decimal_comma():
    assert distance_to_km("27 min\n12,4 km") == 12.4


def test_distance_to_km_handles_meters():
    assert distance_to_km("4 min\n800 m") == 0.8


def test_distance_to_km_returns_none_without_distance():
    assert distance_to_km("27 min") is None


def test_build_maps_url_keeps_commas_in_coordinates():
    url = build_maps_url("51.595993,7.457982", "52.520008,13.404954")

    assert url == (
        "https://www.google.com/maps/dir/51.595993,7.457982/52.520008,13.404954"
    )


def test_build_maps_url_encodes_addresses():
    url = build_maps_url("Bahnhofstraße 1, Lünen", "Berlin Hauptbahnhof")

    assert url.startswith("https://www.google.com/maps/dir/")
    assert "Bahnhofstra%C3%9Fe%201,%20L%C3%BCnen" in url
    assert url.endswith("/Berlin%20Hauptbahnhof")


def test_build_maps_url_strips_whitespace():
    assert build_maps_url("  Lünen ", " Berlin ").endswith("/L%C3%BCnen/Berlin")
