"""Minimal Home Assistant stand-in so the flow logic can be imported and tested.

This is *not* a Home Assistant emulator. It only provides the names ``config_flow.py``
imports, so that the pure parts (validation, cleaning, schema construction) can be tested
on a machine without Home Assistant. Anything that needs the real flow engine remains
untested here - see the README of the test suite.
"""

from __future__ import annotations

import sys
import types
from typing import Any

import voluptuous as vol


def _module(name: str, **attributes: Any) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def install() -> None:
    """Create the fake package hierarchy (idempotent)."""
    if "homeassistant" in sys.modules and getattr(
        sys.modules["homeassistant"], "__fake__", False
    ):
        return

    class ConfigFlow:
        VERSION = 1

        def __init_subclass__(cls, *, domain: str | None = None, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            cls.domain = domain

    class ConfigEntry:
        def __init__(self, **kwargs: Any) -> None:
            self.data = kwargs.get("data", {})
            self.options = kwargs.get("options", {})
            self.title = kwargs.get("title", "")

    class OptionsFlowWithReload:
        automatic_reload = True

    class NumberSelectorConfig:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

    class NumberSelector:
        """Behaves like the real selector: callable, coerces to a number."""

        def __init__(self, config: Any) -> None:
            self.config = config

        def __call__(self, data: Any) -> int | float:
            if isinstance(data, bool) or not isinstance(data, (int, float)):
                raise vol.Invalid("expected a number")
            return int(data) if float(data).is_integer() else float(data)

    class SelectSelectorConfig:
        def __init__(self, options: Any, **kwargs: Any) -> None:
            self.options = options
            self.kwargs = kwargs

    class SelectSelector:
        """Behaves like the real selector: callable, passes the string through."""

        def __init__(self, config: Any) -> None:
            self.config = config

        def __call__(self, data: Any) -> str:
            if not isinstance(data, str):
                raise vol.Invalid("expected a string")
            return data

    class UnitOfTime:
        MINUTES = "min"

    class _Mode:
        BOX = "box"
        DROPDOWN = "dropdown"

    root = _module("homeassistant")
    root.__fake__ = True  # type: ignore[attr-defined]
    root.__path__ = []  # type: ignore[attr-defined]
    helpers = _module("homeassistant.helpers")
    helpers.__path__ = []  # type: ignore[attr-defined]

    _module(
        "homeassistant.config_entries",
        ConfigFlow=ConfigFlow,
        ConfigEntry=ConfigEntry,
        ConfigFlowResult=dict,
        OptionsFlowWithReload=OptionsFlowWithReload,
    )
    _module("homeassistant.const", CONF_NAME="name", UnitOfTime=UnitOfTime)
    _module(
        "homeassistant.core",
        HomeAssistant=type("HomeAssistant", (), {}),
        callback=lambda func: func,
    )
    _module(
        "homeassistant.helpers.aiohttp_client",
        async_get_clientsession=lambda hass: None,
    )
    _module(
        "homeassistant.helpers.selector",
        NumberSelector=NumberSelector,
        NumberSelectorConfig=NumberSelectorConfig,
        NumberSelectorMode=_Mode,
        SelectSelector=SelectSelector,
        SelectSelectorConfig=SelectSelectorConfig,
        SelectSelectorMode=_Mode,
    )
