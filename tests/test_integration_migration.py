"""Tests for the version 1 -> 2 config entry migration.

Migration is the riskiest code path of the update: a wrong mapping costs the user his
entity ids and history, so the mapping is tested explicitly.
"""

from __future__ import annotations

import asyncio
from typing import Any

import _ha_stub_entities

_ha_stub_entities.install()

from _loader import load  # noqa: E402

load("api")
load("location")
load("coordinator")
integration = load("__init__")

async_migrate_entry = integration.async_migrate_entry


class FakeEntry:
    def __init__(self, data: dict[str, Any], title: str = "Arbeitsweg", version: int = 1) -> None:
        self.entry_id = "abc123"
        self.data = data
        self.title = title
        self.version = version
        self.options: dict[str, Any] = {}


class FakeConfigEntries:
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []

    def async_update_entry(self, entry: FakeEntry, **kwargs: Any) -> None:
        self.updates.append(kwargs)
        for key, value in kwargs.items():
            setattr(entry, key, value)


class FakeHass:
    def __init__(self) -> None:
        self.config_entries = FakeConfigEntries()


def run(coro):
    return asyncio.run(coro)


def test_version_1_is_migrated_to_one_trip():
    entry = FakeEntry({"name": "Arbeitsweg", "coordinates": [{"Start": "Zuhause", "End": "Arbeit"}]})
    hass = FakeHass()

    assert run(async_migrate_entry(hass, entry)) is True

    assert entry.version == 2
    assert entry.data == {"name": "Arbeitsweg", "start": "Zuhause", "end": "Arbeit"}
    assert entry.title == "Arbeitsweg"


def test_migration_keeps_entity_ids_by_not_touching_the_unique_id():
    entry = FakeEntry({"name": "Arbeitsweg", "coordinates": [{"Start": "A", "End": "B"}]})
    hass = FakeHass()

    run(async_migrate_entry(hass, entry))

    assert "unique_id" not in hass.config_entries.updates[0]


def test_migration_uses_the_title_when_the_name_is_missing():
    entry = FakeEntry({"coordinates": [{"Start": "A", "End": "B"}]}, title="Uniweg")
    hass = FakeHass()

    assert run(async_migrate_entry(hass, entry)) is True
    assert entry.data["name"] == "Uniweg"
    assert entry.title == "Uniweg"


def test_migration_trims_whitespace():
    entry = FakeEntry({"name": " X ", "coordinates": [{"Start": " A ", "End": " B "}]})
    hass = FakeHass()

    run(async_migrate_entry(hass, entry))

    assert entry.data == {"name": "X", "start": "A", "end": "B"}


def test_entry_without_trip_is_not_migrated():
    entry = FakeEntry({"name": "Kaputt", "coordinates": []})
    hass = FakeHass()

    assert run(async_migrate_entry(hass, entry)) is False
    assert entry.version == 1
    assert hass.config_entries.updates == []


def test_entry_without_start_or_end_is_not_migrated():
    entry = FakeEntry({"name": "Kaputt", "coordinates": [{"Start": "", "End": "B"}]})
    hass = FakeHass()

    assert run(async_migrate_entry(hass, entry)) is False
    assert hass.config_entries.updates == []


def test_current_entry_is_left_alone():
    entry = FakeEntry({"name": "X", "start": "A", "end": "B"}, version=2)
    hass = FakeHass()

    assert run(async_migrate_entry(hass, entry)) is True
    assert hass.config_entries.updates == []


def test_newer_entry_is_refused():
    entry = FakeEntry({"name": "X"}, version=3)
    hass = FakeHass()

    assert run(async_migrate_entry(hass, entry)) is False
    assert hass.config_entries.updates == []
