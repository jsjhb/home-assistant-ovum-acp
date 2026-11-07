"""The Ovum Modbus Integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_DEVICE_ID, CONF_SCAN_INTERVAL

from .hub import OvumModbusHub
from .const import DOMAIN, ATTR_MANUFACTURER, DEFAULT_SCAN_INTERVAL, CONF_ALLOW_ANY_REGISTER, WRITABLE_REGISTERS

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

SERVICE_READ = "read_register"
SERVICE_WRITE = "write_register"

_SCHEMA_READ = vol.Schema({
    vol.Required("name"): str,
    vol.Required("address"): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
    vol.Optional("count", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
})
_SCHEMA_WRITE = vol.Schema({
    vol.Required("name"): str,
    vol.Required("address"): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
    vol.Required("value"): vol.All(vol.Coerce(int), vol.Range(min=-32768, max=65535)),
    vol.Optional("verify", default=True): bool,
})


def _find_entry(hass: HomeAssistant, name: str):
    """Return (entry_id, data) of the hub whose name matches (case-insensitive)."""
    for entry_id, data in hass.data.get(DOMAIN, {}).items():
        hub = data.get("hub")
        if hub and hub.name.strip().lower() == name.strip().lower():
            return entry_id, data
    known = [d["hub"].name for d in hass.data.get(DOMAIN, {}).values() if d.get("hub")]
    raise HomeAssistantError(f"Unknown OVUM unit '{name}'. Known: {known}")


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_WRITE):
        return

    async def _handle_read(call: ServiceCall) -> ServiceResponse:
        _, data = _find_entry(hass, call.data["name"])
        hub = data["hub"]
        values = await hub.read_register_doc(call.data["address"], call.data["count"])
        return {"name": hub.name, "address": call.data["address"], "values": values}

    async def _handle_write(call: ServiceCall) -> ServiceResponse:
        entry_id, data = _find_entry(hass, call.data["name"])
        hub = data["hub"]
        address = call.data["address"]
        entry = hass.config_entries.async_get_entry(entry_id)
        allow_any = bool(entry and entry.options.get(CONF_ALLOW_ANY_REGISTER, False))
        if address not in WRITABLE_REGISTERS and not allow_any:
            raise HomeAssistantError(
                f"Register {address} is not documented as writable by OVUM. Enable "
                f"'allow writing to any register' in the integration options to override.")
        result = await hub.write_register_doc(address, call.data["value"], call.data["verify"])
        result["name"] = hub.name
        if not result.get("ok"):
            raise HomeAssistantError(f"OVUM {hub.name}: write to {address} rejected: {result.get('error')}")
        return result

    hass.services.async_register(DOMAIN, SERVICE_READ, _handle_read,
                                 schema=_SCHEMA_READ, supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, SERVICE_WRITE, _handle_write,
                                 schema=_SCHEMA_WRITE, supports_response=SupportsResponse.OPTIONAL)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Ovum Modbus component."""
    hass.data.setdefault(DOMAIN, {})
    _register_services(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Ovum Modbus entry."""
    hub = await _create_hub(hass, entry)
    
    if not hub:
        return False

    hass.data[DOMAIN][entry.entry_id] = {
        "hub": hub,
        "device_info": _create_device_info(entry)
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await hass.data[DOMAIN][entry.entry_id]["hub"].close()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)

async def _create_hub(hass: HomeAssistant, entry: ConfigEntry) -> OvumModbusHub:
    """Helper function to create the Ovum Modbus hub."""
    try:
        hub = OvumModbusHub(
            hass,
            entry.data[CONF_NAME],
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data[CONF_DEVICE_ID],
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        await hub.async_config_entry_first_refresh()
        return hub
    except Exception as e:
        _LOGGER.error(f"Failed to set up Ovum Modbus hub: {e}")
        return None

def _create_device_info(entry: ConfigEntry) -> dict:
    """Create the device info for Ovum Modbus hub."""
    return {
        "identifiers": {(DOMAIN, entry.data[CONF_NAME])},
        "name": entry.data[CONF_NAME],
        "manufacturer": ATTR_MANUFACTURER
    }
