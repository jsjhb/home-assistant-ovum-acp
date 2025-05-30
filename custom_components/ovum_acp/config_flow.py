import ipaddress
import re
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SLAVE, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
import logging

from .const import DEFAULT_NAME, DEFAULT_PORT, DEFAULT_SLAVE, DEFAULT_SCAN_INTERVAL, DOMAIN
from .hub import OvumModbusHub

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): int,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
})

#OPTIONS_SCHEMA = vol.Schema({
#    vol.Required(CONF_HOST): str,
#    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
#    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
#})

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
    return {entry.data[CONF_HOST] for entry in hass.config_entries.async_entries(DOMAIN)}

class OvumModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Ovum Modbus configflow."""
    VERSION = 1
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
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow to allow configuration changes after setup."""
        return OvumModbusOptionsFlowHandler(config_entry)


class OvumModbusOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Ovum Modbus."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            try:
                # Get the hub from the saved data
                hub = self.hass.data[DOMAIN].get(self.config_entry.entry_id, {}).get("hub")

                if hub is None:
                    _LOGGER.error(f"Hub not found for entry_id: {self.config_entry.entry_id}")
                    return self.async_abort(reason="hub_not_found")

                # Update the hub configuration
                await hub.update_connection_settings(user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_SLAVE], user_input[CONF_SCAN_INTERVAL])

                # Save the new options in the configuration entry
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, **user_input},
                )

                return self.async_create_entry(title="", data=user_input)
            except Exception as e:
                _LOGGER.error(f"Error updating Ovum Modbus configuration: {str(e)}")
                return self.async_abort(reason="update_failed")

        # Show the options form
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=self.config_entry.data.get(CONF_HOST, '')): str,
                vol.Required(CONF_PORT, default=self.config_entry.data.get(CONF_PORT, 502)): int,
                vol.Required(CONF_SLAVE, default=self.config_entry.data.get(CONF_SLAVE, 247)): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=self.config_entry.data.get(CONF_SCAN_INTERVAL, 30)): int,
            }),
        )
