"""Module defining constants for the custom integration 'my_electricity'."""

# Define constants for the custom integration

DOMAIN = "my_electricity"
VERSION = "1.0"

# Configuration keys
CONF_SUBSCRIPTION_KEY = "subscription_key"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

# API Endpoints
API_URL = "https://api.open.helen.fi/electricity-retail/v2/time-series"

# Rate limiting
RATE_LIMIT = 20  # Maximum calls per minute

# Default values
DEFAULT_UPDATE_INTERVAL = 30  # Default update interval in minutes

# Logging and error messages
LOG_INITIALIZED = "Initialized ElectricitySensor for meter_point_id: {}"
LOG_FETCHING_DATA = "Fetching data for meter_point_id: {}"
LOG_RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again later."
LOG_API_RESPONSE_ERROR = "HTTP error occurred: {}"
LOG_CONNECTION_ERROR = "Connection error occurred: {}"
LOG_TIMEOUT_ERROR = "Timeout error occurred: {}"
LOG_REQUEST_ERROR = "Request error occurred: {}"
LOG_METER_POINT_NOT_FOUND = "Meter point ID {} not found in response."
