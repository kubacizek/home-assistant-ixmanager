"""Constants for the iXmanager integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

# Domain
DOMAIN: Final = "ixmanager"

# API Configuration
BASE_URL: Final = "https://evcharger.ixcommand.com/api/v1"
API_TIMEOUT: Final = 30
UPDATE_INTERVAL: Final = timedelta(seconds=30)

# Configuration keys
CONF_API_KEY: Final = "api_key"
CONF_SERIAL_NUMBER: Final = "serial_number"
CONF_CABLE_TYPE: Final = "cable_type"

# Device properties
PROPERTY_CHARGING_ENABLE: Final = "chargingEnable"
PROPERTY_MAXIMUM_CURRENT: Final = "maximumCurrent"
PROPERTY_CURRENT_CHARGING_POWER: Final = "currentChargingPower"
PROPERTY_TOTAL_ENERGY: Final = "totalEnergy"
PROPERTY_SINGLE_PHASE: Final = "singlePhase"
PROPERTY_SIGNAL: Final = "signal"
PROPERTY_CHARGING_STATUS: Final = "chargingStatus"
PROPERTY_TARGET_CURRENT: Final = "targetCurrent"
PROPERTY_CHARGING_CURRENT: Final = "chargingCurrent"
PROPERTY_CHARGING_CURRENT_L2: Final = "chargingCurrentL2"
PROPERTY_CHARGING_CURRENT_L3: Final = "chargingCurrentL3"

# Cable types and specifications
CABLE_TYPE_16A: Final = "16A"
CABLE_TYPE_32A: Final = "32A"

CABLE_TYPES: Final = {
    CABLE_TYPE_16A: {
        "name": "Type 2 Cable (16A Max)",
        "max_current": 16,
        "description": "Standard charging cable, maximum 16A",
    },
    CABLE_TYPE_32A: {
        "name": "Type 2 Cable (32A Max)",
        "max_current": 32,
        "description": "High power charging cable, maximum 32A",
    },
}

# Default values
DEFAULT_NAME: Final = "iXmanager"
DEFAULT_CABLE_TYPE: Final = CABLE_TYPE_16A
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=1)

# Platforms
PLATFORMS: Final = ["sensor", "switch", "number"]
