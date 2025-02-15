# Ovum ACP - A Home Assistant integration for Ovum ACP heat pumps

Integration for reading data from Ovum ACP heat pumps through Modbus TCP, either directly or through EPoCa module.

Implements reading modbus registers published in [Ovum's documentation page](https://susi.ovum.at). Developed according to [modbus register map for AC208P](https://github.com/jsjhb/home-assistant-ovum-acp/blob/main/Anleitung_ModBusTCP_AirCubeACP_DE_240705.pdf)

## Features

- Installation through Config Flow UI
- Officially published registers (power, energy, temperature sensors)
- Configurable polling interval - changeable at any time

## Installation

This integration can be installed using a custom repository in HACS. Add the repository https://github.com/jsjhb/home-assisitant-ovum-acp to HACS and search for "Ovum ACP", click it and click "Download". Don't forget to restart Home-Assistant. After restart, this integration can be configured through the integration setup UI.

## Configuration

1. Navigate to the "Integrations" page in your configuration, then click "Add Integration" and select "Ovum ACP".
2. Enter the IP Address, Modbus port, unit id and interval.

