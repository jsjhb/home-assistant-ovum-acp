import ipaddress
import re
import voluptuous as vol
from typing import Any
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_DEVICE_ID, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
import logging

from .const import (
    DEFAULT_CONFIG_SCHEMA,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_DEVICE_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .cfgutils import get_config_value, get_config_values

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=60, msg="invalid_scan_interval")
        ),
    }
)

ERROR_ALREADY_CONFIGURED = "already_configured"
ERROR_INVALID_HOST = "invalid_host"

def host_valid(host):
    """Return True if hostname or IP address is valid."""
    try:
        ip_version = ipaddress.ip_address(host).version
        return ip_version in [4, 6]
    except ValueError:
        disallowed = re.compile(r"[^a-zA-Z\d\-]")
        return all(x and not disallowed.search(x) for x in host.split("."))

@callback
def ovum_modbus_entries(hass: HomeAssistant):
    """Return the hosts already configured."""
    return {
        get_config_value(entry, CONF_HOST)
        for entry in hass.config_entries.async_entries(DOMAIN)
    }

class OvumModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Ovum Modbus configflow."""
    VERSION = 1
    # ?
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def _host_in_configuration_exists(self, host) -> bool:
        """Return True if host exists in configuration."""
        return host in ovum_modbus_entries(self.hass)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]

            if self._host_in_configuration_exists(host):
                errors[CONF_HOST] = ERROR_ALREADY_CONFIGURED
            elif not host_valid(host):
                errors[CONF_HOST] = ERROR_INVALID_HOST
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow to allow configuration changes after setup."""
        return OvumModbusOptionsFlowHandler(config_entry)


class OvumModbusOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Ovum Modbus."""

    def _current(self) -> dict[str, Any]:
        """Current value of every config key: options -> data -> schema default.

        Single source of truth for reading; DEFAULT_CONFIG_SCHEMA in const.py
        owns the defaults, so they cannot drift between the options form and
        the hub (__init__.py reads the same table via get_config_values()).
        Callers apply their own policy on top - this only reads.
        """
        return get_config_values(self.config_entry, DEFAULT_CONFIG_SCHEMA)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            # user_input wins for every key it carries; anything it omits keeps
            # the entry's current value. Same semantics as the per-key
            # setdefault() chain this replaces, but the defaults now come from
            # DEFAULT_CONFIG_SCHEMA instead of being re-spelled as literals.
            merged = {**self._current(), **user_input}

            # Enforce minimum scan interval of 30s. Note the asymmetry with
            # _get_options_schema(), which clamps instead: a legacy entry below
            # the minimum should not block opening the form, but actively
            # submitting such a value is an error worth showing.
            if merged[CONF_SCAN_INTERVAL] < 30:
                errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"

            if not errors:
                return self.async_create_entry(title="", data=merged)

        return self.async_show_form(
            step_id="init", data_schema=self._get_options_schema(), errors=errors
        )
 
