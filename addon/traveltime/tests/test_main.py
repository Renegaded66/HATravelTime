from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import duration_to_minutes, DURATION_PATTERN, DISTANCE_PATTERN


def test_duration_to_minutes_supports_minutes():
    assert duration_to_minutes("27 min") == 27


def test_duration_to_minutes_supports_hours_and_minutes():
    assert duration_to_minutes("2 h 31 min") == 151


def test_current_google_maps_route_card_fixture_contains_duration_and_distance():
    text = Path(__file__).with_name("google_maps_route_text.txt").read_text(encoding="utf-8")

    assert DURATION_PATTERN.search(text)
    assert DISTANCE_PATTERN.search(text)
    assert duration_to_minutes(text) == 27
