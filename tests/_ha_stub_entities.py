"""Extra Home Assistant stand-ins for the entity and coordinator modules.

Only used by ``test_integration_entities.py``. Together with ``_ha_stub`` this is enough to
import ``coordinator.py``, ``sensor.py`` and ``button.py`` and to check the declarative
entity metadata - above all the unique ids, because they decide whether an existing
installation keeps its entity ids and history.
"""

from __future__ import annotations

import sys
import types
from typing import Any

import _ha_stub


def _module(name: str, **attributes: Any) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def install() -> None:
    """Extend the base stub with the names the entity modules import."""
    _ha_stub.install()
    if "homeassistant.components.sensor" in sys.modules:
        return

    class _DeviceClass:
        DURATION = "duration"
        TIMESTAMP = "timestamp"

    class _StateClass:
        MEASUREMENT = "measurement"

    class _Category:
        DIAGNOSTIC = "diagnostic"

    class SensorEntity:
        pass

    class ButtonEntity:
        pass

    class CoordinatorEntity:
        def __init__(self, coordinator: Any) -> None:
            self.coordinator = coordinator

        def __class_getitem__(cls, item: Any) -> Any:
            return cls

        @property
        def available(self) -> bool:
            return True

    class DataUpdateCoordinator:
        def __class_getitem__(cls, item: Any) -> Any:
            return cls

        def __init__(self, hass: Any, logger: Any, **kwargs: Any) -> None:
            self.hass = hass
            self.logger = logger
            self.kwargs = kwargs
            self.data = None
            self.last_update_success = True

    class UpdateFailed(Exception):
        pass

    class DeviceInfo(dict):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self.__dict__.update(kwargs)

    components = _module("homeassistant.components")
    components.__path__ = []  # type: ignore[attr-defined]

    _module(
        "homeassistant.components.sensor",
        SensorEntity=SensorEntity,
        SensorDeviceClass=_DeviceClass,
        SensorStateClass=_StateClass,
    )
    _module("homeassistant.components.button", ButtonEntity=ButtonEntity)
    _module(
        "homeassistant.helpers.update_coordinator",
        CoordinatorEntity=CoordinatorEntity,
        DataUpdateCoordinator=DataUpdateCoordinator,
        UpdateFailed=UpdateFailed,
    )
    _module("homeassistant.helpers.device_registry", DeviceInfo=DeviceInfo)
    _module(
        "homeassistant.helpers.entity_platform",
        AddEntitiesCallback=type("AddEntitiesCallback", (), {}),
    )
    _module(
        "homeassistant.helpers.entity",
        EntityCategory=_Category,
    )
    _module("homeassistant.util")
    _module(
        "homeassistant.util.dt",
        utcnow=lambda: __import__("datetime").datetime(2026, 10, 25, 12, 0, tzinfo=__import__("datetime").timezone.utc),
    )
