"""Config, options and reconfigure flow for the Travel Time integration.

All three flows ask for everything on a single page: name, start and destination.
Start and destination are combo boxes: they list every ``person``, ``zone``,
``device_tracker`` and coordinate carrying ``sensor`` plus all other entities, and you can
simply type an address instead.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import async_probe_addon
from .const import (
    CONF_END,
    CONF_SCAN_INTERVAL,
    CONF_START,
    CONFIG_VERSION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
)
from .location import (
    LocationError,
    MissingCoordinatesError,
    UnknownEntityError,
    location_options,
    resolve_location,
)

_LOGGER = logging.getLogger(__name__)

LOCATION_KEYS = (CONF_START, CONF_END)


def _validate_locations(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:
    """Check name and both endpoints, returning field specific error keys."""
    errors: dict[str, str] = {}

    if not (user_input.get(CONF_NAME) or "").strip():
        errors[CONF_NAME] = "name_required"

    for key in LOCATION_KEYS:
        value = (user_input.get(key) or "").strip()
        if not value:
            errors[key] = "no_location"
            continue
        try:
            resolve_location(value, hass.states)
        except UnknownEntityError:
            errors[key] = "entity_not_found"
        except MissingCoordinatesError:
            errors[key] = "entity_no_coordinates"
        except LocationError:
            errors[key] = "no_location"

    return errors


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    """Strip whitespace and normalise the submitted values."""
    try:
        interval = int(user_input.get(CONF_SCAN_INTERVAL) or 0)
    except (TypeError, ValueError):
        interval = DEFAULT_SCAN_INTERVAL
    return {
        CONF_NAME: (user_input.get(CONF_NAME) or "").strip(),
        CONF_START: (user_input.get(CONF_START) or "").strip(),
        CONF_END: (user_input.get(CONF_END) or "").strip(),
        CONF_SCAN_INTERVAL: min(max(interval, 0), MAX_SCAN_INTERVAL),
    }


def _location_selector(hass: HomeAssistant) -> SelectSelector:
    """Combo box with all entities that carry coordinates - typing an address also works."""
    return SelectSelector(
        SelectSelectorConfig(
            options=location_options(hass.states.async_all()),
            custom_value=True,
            mode=SelectSelectorMode.DROPDOWN,
            sort=False,
        )
    )


def _schema(hass: HomeAssistant, current: dict[str, Any]) -> Any:
    """Build the one-page form."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=current.get(CONF_NAME, "")): str,
            vol.Required(CONF_START, default=current.get(CONF_START, "")): (
                _location_selector(hass)
            ),
            vol.Required(CONF_END, default=current.get(CONF_END, "")): (
                _location_selector(hass)
            ),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=int(current.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=MAX_SCAN_INTERVAL,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement=UnitOfTime.MINUTES,
                )
            ),
        }
    )


class TravelTimeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create a new trip."""

    VERSION = CONFIG_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> TravelTimeOptionsFlow:
        """Return the options flow used by the "Configure" button."""
        return TravelTimeOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the single setup page."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _clean(user_input)
            errors = _validate_locations(self.hass, data)

            if not errors:
                # The add-on is mandatory: tell the user right away instead of
                # creating an entry that can never produce a value.
                session = async_get_clientsession(self.hass)
                if not await async_probe_addon(session):
                    errors["base"] = "addon_unreachable"

            if not errors:
                await self.async_set_unique_id(data[CONF_NAME])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(self.hass, _clean(user_input or {})),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit an existing trip ("Neu konfigurieren")."""
        entry = self._get_reconfigure_entry()
        current = {**entry.data, **entry.options}

        if user_input is not None:
            data = _clean(user_input)
            errors = _validate_locations(self.hass, data)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, title=data[CONF_NAME], options=data
                )
        else:
            data = current
            errors = {}

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(self.hass, data),
            errors=errors,
        )


class TravelTimeOptionsFlow(OptionsFlowWithReload):
    """Edit an existing trip from the entry menu ("Konfigurieren")."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the single edit page."""
        entry = self.config_entry
        current = {**entry.data, **entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _clean(user_input)
            errors = _validate_locations(self.hass, data)
            if not errors:
                if data[CONF_NAME] != entry.title:
                    self.hass.config_entries.async_update_entry(entry, title=data[CONF_NAME])
                return self.async_create_entry(title="", data=data)
        else:
            data = current

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(self.hass, data),
            errors=errors,
        )
