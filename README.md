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

## Additional notes

Development of the integration is heavily influenced and derived from [SAJ H2 Inverter Modbus](https://github.com/stanus74/home-assistant-saj-h2-modbus). Thanks to stanus74!

This integration is in no way endorsed or supported by OVUM Wärmepumpen GmbH. OVUM chose not to answer any requests with respect to this integration.

Information for reading values via Modbus stems from the above mentioned register map. In the supplied version of the document are several errors, which have been identified, values are read and interpreted in the correct way.
