"""Module provides a sensor for electricity usage data from the Helen API."""

from datetime import timedelta  # Correct import here
import logging
import time

import aiohttp

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, StateType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HelenApi  # Import the updated API class

_LOGGER = logging.getLogger(__name__)


class RateLimiter:
    """Class to handle rate limiting."""

    RATE_LIMIT = 20  # Maximum calls per minute

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        self.last_called_times: list[float] = []

    def rate_limit(self):
        """Implement rate limiting to ensure compliance with API restrictions."""
        current_time = time.time()
        # Remove timestamps older than 60 seconds
        self.last_called_times = [
            t for t in self.last_called_times if current_time - t < 60
        ]
        if len(self.last_called_times) >= self.RATE_LIMIT:
            _LOGGER.warning("Rate limit exceeded. Please try again later")
            raise UpdateFailed("Rate limit exceeded. Please try again later.")
        self.last_called_times.append(current_time)
        _LOGGER.debug(
            "Rate limit check passed. Current API call count: %d",
            len(self.last_called_times),
        )


rate_limiter = RateLimiter()


class ElectricitySensor(SensorEntity):
    """Sensor for Electricity Usage Data."""

    def __init__(self, coordinator, meter_point_id, api: HelenApi) -> None:
        """Initialize the Electricity Usage sensor."""
        self.coordinator = coordinator
        self.api = api
        self.meter_point_id = meter_point_id

        self._attr_name = f"Electricity Usage ({meter_point_id})"
        self._attr_unique_id = f"electricity_usage_{meter_point_id}"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

        _LOGGER.info(
            "Initialized ElectricitySensor for meter_point_id: %s", meter_point_id
        )

    @property
    def native_value(self) -> StateType | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.meter_point_id)

    async def async_update(self) -> None:
        """Update the sensor state."""
        _LOGGER.debug("Updating state for meter_point_id: %s", self.meter_point_id)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor from a config entry."""
    subscription_key: str = config_entry.data["subscription_key"]
    client_secret: str = config_entry.data["client_secret"]
    customer_id: str = config_entry.data["client_id"]

    # Create an instance of HelenApi
    api = HelenApi(
        subscription_key=subscription_key,
        client_secret=client_secret,
        meter_point_id=None,
        customer_id=customer_id,
    )

    # Authenticate with the Helen API
    if not await api.authenticate():
        _LOGGER.error("Failed to authenticate with Helen API")
        return

    # Fetch metering points
    metering_points = await api.fetch_metering_points()
    if not metering_points:
        _LOGGER.error(
            "No metering points found for customer_id: %s", customer_id
        )  # Correct variable name here
        return

    entities = []

    for meter_point_id in metering_points:

        async def async_update_data(meter_point_id=meter_point_id):
            """Fetch data from Helen API."""
            rate_limiter.rate_limit()  # Apply rate limiting before making the request
            try:
                data = await api.fetch_usage(meter_point_id)
                time_series = data.get("timeSeriesResult", {}).get("timeSeries", {})
                if time_series:
                    usage_sum = time_series.get("sum")
                    _LOGGER.info(
                        "Fetched electricity usage sum for meter_point_id: %s: %s",
                        meter_point_id,
                        usage_sum,
                    )
                    return {meter_point_id: usage_sum}

                _LOGGER.error("Meter point ID %s not found in response", meter_point_id)
                raise UpdateFailed(
                    f"Meter point ID {meter_point_id} not found in response"
                )
            except aiohttp.ClientError as err:
                raise UpdateFailed(f"Error fetching data: {err}") from err

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"electricity usage {meter_point_id}",
            update_method=async_update_data,
            update_interval=timedelta(days=1),  # Update once a day
        )

        await coordinator.async_refresh()
        entities.append(ElectricitySensor(coordinator, meter_point_id, api))

    async_add_entities(entities)
