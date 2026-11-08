"""The Ovum Modbus Integration."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    Platform,
)
from .const import (
    DOMAIN,
    ATTR_MANUFACTURER,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_CONFIG_SCHEMA,
    CONF_MODBUSDEVICE,
)
from homeassistant.helpers import config_validation as cv
from .cfgutils import get_config_value, get_config_values

if TYPE_CHECKING:
    from .hub import OvumModbusHub, OvumConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    #Platform.NUMBER,
    #Platform.TEXT,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Ovum Modbus component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: OvumConfigEntry) -> bool:
    """Set up a Ovum Modbus entry."""
    _LOGGER.debug("Starting async_setup_entry")
    start_time = time.monotonic()

    hub = await _create_hub(hass, entry)
    hub.device_info = _create_device_info(entry)
    _update_device_info_from_hub_data(hub)
    entry.runtime_data = hub
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    end_time = time.monotonic()
    elapsed_time = end_time - start_time
    _LOGGER.debug(f"async_setup_entry completed in {elapsed_time:.2f} seconds")

    return True

async def async_unload_entry(hass: HomeAssistant, entry: OvumConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if not unload_ok:
        # Entities of the platforms that failed to unload are still running,
        # and HA keeps the entry (and its update listener) loaded as well, so
        # the hub they depend on has to stay up until the next restart.
        _LOGGER.warning(
            "Unload platforms failed for entry %s; keeping the hub running",
            entry.entry_id,
        )
        return False

    hub = getattr(entry, "runtime_data", None)
    if hub is not None:
        try:
            await hub.async_unload_entry()
        except Exception as e:
            _LOGGER.debug(f"Ignoring hub unload error: {e}")

    return True

async def async_update_options(hass: HomeAssistant, entry: OvumConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)

async def _create_hub(hass: HomeAssistant, entry: OvumConfigEntry) -> OvumModbusHub:
    """Helper function to create the Ovum Modbus hub."""
    scan_interval = get_config_value(entry, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    _LOGGER.info(f"Setting scan interval to {scan_interval} seconds")
    _LOGGER.info("Starting hub with first refresh...")

    from .hub import OvumModbusHub

    hub = OvumModbusHub(
        hass,
        entry, # Pass the full ConfigEntry object
    )

    try:
        await hub.async_config_entry_first_refresh()
    except BaseException:
        # The constructor already started the cache cleanup timer
        # HA retries a failed setup with a fresh hub, so without this teardown every
        # retry while the inverter is unreachable would leak another set.
        try:
            await hub.async_unload_entry()
        except Exception as cleanup_err:
            _LOGGER.debug("Ignoring hub teardown error: %s", cleanup_err)
        raise
    _LOGGER.info(
        f"Hub first refresh completed, coordinator should run every {scan_interval} seconds"
    )
    
    return hub

def _create_device_info(entry: ConfigEntry) -> dict:
    """Create the device info for Ovum Modbus hub."""
    return {
        "identifiers": {(DOMAIN, entry.data[CONF_NAME])},
        "name": entry.data[CONF_NAME],
        "manufacturer": ATTR_MANUFACTURER,
        "model": "ACP",
    }

def _update_device_info_from_hub_data(hub: OvumModbusHub) -> None:
    """Enrich device info with firmware/hardware data after first refresh."""
    data = hub.firmware_data
    if not data:
        return

#    sw_version = _join_version(data, "dv", "mcv", "scv")
    sw_version = data.get("firmware_data")
    if sw_version:
        hub.device_info["sw_version"] = str(data.get("firmware_data"))

#    hw_version = _join_version(data, "disphwversion", "ctrlhwversion", "powerhwversion")
#    if hw_version:
#        hub.device_info["hw_version"] = hw_version
#
#    model = data.get("devtype")
#    if model is not None:
#        hub.device_info["model"] = f"Ovum ACP ({model})"
