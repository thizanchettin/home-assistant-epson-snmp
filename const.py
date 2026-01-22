"""
Constants for the Epson SNMP integration.

This module centralizes:
- Domain and configuration keys
- Default values for configuration options
- Profile identifiers

Keeping these definitions here avoids string duplication and ensures
consistency across config flow, coordinator, and platforms.
"""

DOMAIN = "epson_snmp"

# Configuration keys
CONF_HOST = "host"
CONF_NAME = "name"
CONF_COMMUNITY = "community"
CONF_VERSION = "version"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_PROFILE = "profile"

# Default values
DEFAULT_NAME = "Epson Printer"
DEFAULT_COMMUNITY = "public"
DEFAULT_VERSION = "2c"
DEFAULT_SCAN_INTERVAL = 30

# Profile identifiers
PROFILE_AUTO = "auto"
PROFILE_GENERIC = "generic"
