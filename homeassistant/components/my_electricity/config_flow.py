"""Config flow for Electricity Usage integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_SUBSCRIPTION_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Adjust the data schema to collect necessary input from the user
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SUBSCRIPTION_KEY): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
    }
)


class PlaceholderHub:
    """Placeholder class to simulate connection."""

    def __init__(
        self, subscription_key: str, client_id: str, client_secret: str
    ) -> None:
        """Initialize."""
        self.subscription_key = subscription_key
        self.client_id = client_id
        self.client_secret = client_secret

    async def authenticate(self) -> bool:
        """Simulate an authentication check."""
        # Here you would use the credentials to authenticate with the Helen API
        # In this placeholder, we assume it always succeeds
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    hub = PlaceholderHub(
        data[CONF_SUBSCRIPTION_KEY], data[CONF_CLIENT_ID], data[CONF_CLIENT_SECRET]
    )

    # Simulate an authentication check
    if not await hub.authenticate():
        raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Helen Electricity Usage"}


class ElectricityUsageConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Electricity Usage."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid authentication."""
