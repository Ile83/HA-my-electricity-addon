"""API client for Helen electricity usage data."""

import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class HelenApi:
    """API client for Helen electricity usage data."""

    def __init__(
        self,
        subscription_key: str,
        client_secret: str,
        meter_point_id: str | None = None,
        customer_id: str | None = None,
    ) -> None:
        """Initialize the API client with necessary credentials."""
        self.subscription_key = subscription_key
        self.client_secret = client_secret
        self.meter_point_id = meter_point_id
        self.customer_id = customer_id
        self.base_url = "https://api.open.helen.fi/electricity-retail/v2"
        self.token = None

    async def authenticate(self) -> bool:
        """Authenticate with the API and obtain an access token."""
        auth_url = "https://api.open.helen.fi/authentication/v2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": self.customer_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    auth_url, headers=headers, data=data
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        self.token = response_data.get("access_token")
                        _LOGGER.info("Successfully authenticated with Helen API")
                        return True
                    _LOGGER.error(
                        "Failed to authenticate with Helen API: %s, Response: %s",
                        response.status,
                        await response.text(),
                    )
                    return False
            except aiohttp.ClientError as error:
                _LOGGER.error("Client error during authentication: %s", error)
                return False

    async def fetch_metering_points(self) -> list[str]:
        """Fetch all available metering points."""

        if not self.token:
            _LOGGER.error("Cannot fetch metering points without an access token")
            return []

        url = f"{self.base_url}/metering-points"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        _LOGGER.info(
                            "Successfully fetched metering points for customer %s",
                            self.customer_id,
                        )
                        return response_data[0].get("meteringPointIds", [])
                    if response.status == 403:
                        response_data = await response.json()
                        _LOGGER.error(
                            "Failed to fetch metering points: %s, Response: %s",
                            response.status,
                            response_data,
                        )
                        if (
                            "quota will be replenished"
                            in response_data.get("message", "").lower()
                        ):
                            _LOGGER.warning(
                                "API quota exceeded. Waiting for quota to replenish"
                            )
                        return []
                    _LOGGER.error(
                        "Failed to fetch metering points: %s, Response: %s",
                        response.status,
                        await response.text(),
                    )
                    return []
            except aiohttp.ClientError as error:
                _LOGGER.error("Client error while fetching metering points: %s", error)
                return []

    async def fetch_usage(self, meter_point_id: str) -> dict:
        """Fetch electricity usage data for a specific metering point."""
        if not self.token:
            _LOGGER.error("Cannot fetch data without an access token")
            return {}

        url = f"{self.base_url}/time-series"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }
        params = {
            "meteringPointId": meter_point_id,
            "startTime": "2023-01-01T00:00:00Z",
            "endTime": "2023-12-31T23:59:59Z",
            "resultStep": "DAY",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        _LOGGER.info(
                            "Successfully fetched usage data for meter point %s",
                            meter_point_id,
                        )
                        return response_data
                    _LOGGER.error(
                        "Failed to fetch usage data: %s, Response: %s",
                        response.status,
                        await response.text(),
                    )
                    return {}
            except aiohttp.ClientError as error:
                _LOGGER.error("Client error while fetching data: %s", error)
                return {}
