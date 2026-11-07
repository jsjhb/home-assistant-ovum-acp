# OVUM ACP - A Home Assistant integration for OVUM ACP heat pumps

Integration for reading data from OVUM ACP heat pumps through Modbus TCP, either directly or through EPoCa module.

Implements reading modbus registers published in [OVUM's documentation page](https://susi.ovum.at). Developed according to [modbus register map for AC208P](https://github.com/jsjhb/home-assistant-ovum-acp/blob/main/Anleitung_ModBusTCP_AirCubeACP_DE_240705.pdf)

## Features

- Installation through Config Flow UI
- Officially published registers (power, energy, temperature sensors)
- Configurable polling interval - changeable at any time

## Installation

This integration can be installed using a custom repository in HACS. Add the repository https://github.com/jsjhb/home-assistant-ovum-acp to HACS and search for "OVUM ACP", click it and click "Download". Don't forget to restart Home-Assistant. After restart, this integration can be configured through the integration setup UI.

## Configuration

1. Navigate to the "Integrations" page in your configuration, then click "Add Integration" and select "OVUM ACP".
2. Enter the IP Address, Modbus port, unit id and interval.

## Services: reading and writing registers

The integration provides two services for direct register access. Addresses
are given exactly as in OVUM's Modbus documentation (1-based); the
integration subtracts 1 to get the Modbus protocol address. Values are raw
signed 16-bit integers, e.g. temperatures in tenths of a degree.

Both services use the same Modbus connection as the polling cycle, because
the controller accepts only one Modbus TCP client at a time.

`ovum_acp.read_register` returns the raw values:

```yaml
action: ovum_acp.read_register
data:
  name: Ovum        # name of the config entry
  address: 524      # Raumsolltemperatur Heizkreis 1
  count: 1
response_variable: result
```

`ovum_acp.write_register` writes one register, reads it back and returns
`before`, `after` and `verified`:

```yaml
action: ovum_acp.write_register
data:
  name: Ovum
  address: 524
  value: 215        # 21.5 °C
```

By default only the registers documented as R/W in OVUM's list
"Anleitung ModBusTCP ab Software V241122" (20250527) are accepted (see
`WRITABLE_REGISTERS` in `const.py`). Writing to other addresses can be
enabled per device in the integration options ("allow writing to any
register"). Do this only if you know what the register does — OVUM states
that writing undocumented addresses can damage the unit.

## Additional notes

Development of the integration is heavily influenced and derived from [SAJ H2 Inverter Modbus](https://github.com/stanus74/home-assistant-saj-h2-modbus). Thanks to stanus74!

This integration is in no way endorsed or supported by OVUM Wärmepumpen GmbH. OVUM chose not to answer any requests with respect to this integration.

Information for reading values via Modbus stems from the above mentioned register map. In the supplied version of the document are several errors, which have been identified, values are read and interpreted in the correct way.
