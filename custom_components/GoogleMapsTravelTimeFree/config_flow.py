"""Config flow for the Google Maps Travel Time Free (No Api Key) integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Schema für die Benutzereingabe
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
    }
)

# Schema für die Koordinaten
STEP_COORDINATES_SCHEMA = vol.Schema(
    {
        vol.Required("Start"): vol.Coerce(str),
        vol.Required("End"): vol.Coerce(str),
    }
)


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Maps Travel Time Free (No Api Key)."""

    VERSION = 1
    data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.data = user_input
            return await self.async_step_coordinates()
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_coordinates(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.data.setdefault("coordinates", []).append(user_input)
            # Wenn Benutzer zu Ende ist (z. B. kein „Weiter hinzufügen“ gewünscht)
            await self.async_set_unique_id(self.data[CONF_NAME])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=self.data[CONF_NAME], data=self.data)
        return self.async_show_form(
            step_id="coordinates",
            data_schema=STEP_COORDINATES_SCHEMA,
            errors=errors,
            last_step=True,
        )

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle import from YAML."""
        if user_input is not None:
            self.data = user_input
            # Beispiel: eindeutige ID aus Name (oder kombiniere Koordinaten für Einzigartigkeit)
            await self.async_set_unique_id(self.data[CONF_NAME])
            self._abort_if_unique_id_configured()
            return await self.async_step_coordinates()

        return self.async_abort(reason="no_config")
