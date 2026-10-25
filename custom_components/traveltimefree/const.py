"""Constants for the Travel Time integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "traveltime"
NAME: Final = "Travel Time"

# Configuration keys
CONF_START: Final = "start"
CONF_END: Final = "end"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Config entry version. Version 2 stores exactly one trip per entry and can be edited
# with the options flow. Version 1 stored {"name": ..., "coordinates": [{"Start","End"}]}.
CONFIG_VERSION: Final = 2

# Companion add-on (slug "travel_time", host network, port 6730).
ADDON_URL: Final = "http://127.0.0.1:6730"
ADDON_REQUEST_TIMEOUT: Final = 120  # seconds - a scrape usually takes 5-30 s
ADDON_PROBE_TIMEOUT: Final = 5  # seconds - fast reachability check during setup

# Domains whose entities can carry coordinates and are offered in the location picker.
COORDINATE_DOMAINS: Final = ("person", "zone", "device_tracker", "sensor")

# Update interval in minutes. 0 keeps the historic behaviour: refresh only on button press.
DEFAULT_SCAN_INTERVAL: Final = 0
MAX_SCAN_INTERVAL: Final = 1440
