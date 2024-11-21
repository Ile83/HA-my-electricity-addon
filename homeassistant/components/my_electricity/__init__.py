"""The Electricity Usage integration."""

from __future__ import annotations

import logging
from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import HelenApi  # api.py that defines HelenApi.

_LOGGER = logging.getLogger(__name__)

# List the platforms that you want to support.
PLATFORMS: list[Platform] = [Platform.SENSOR]


# Create ConfigEntry type alias with API object
class ElectricityUsageRuntimeData(TypedDict):
    """TypedDict for storing runtime data including the Helen API instance."""

    api: HelenApi


# Create a type alias for the ConfigEntry
ElectricityConfigEntry = ConfigEntry[ElectricityUsageRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: ElectricityConfigEntry) -> bool:
    """Set up Electricity Usage from a config entry."""
    # 1. Create an API instance
    api = HelenApi(
        subscription_key=entry.data["subscription_key"],
        client_secret=entry.data["client_secret"],
        customer_id=entry.data[
            "client_id"
        ],  # Use the correct key to match config_flow.py
    )

    # 2. Validate the API connection (and authentication)
    if not await api.authenticate():
        _LOGGER.error("Failed to authenticate with Helen API")
        return False

    # 3. Fetch metering points
    metering_points = await api.fetch_metering_points()
    if not metering_points:
        _LOGGER.error(
            "No metering points found for customer_id: %s", entry.data["client_id"]
        )
        return False

    # Store the API object for your platforms to access
    entry.runtime_data = ElectricityUsageRuntimeData(api=api)

    # Forward entry setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ElectricityConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
