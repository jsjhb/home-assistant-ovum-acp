import asyncio
import logging
import time
from datetime import timedelta
from typing import List, Callable, Any, Dict, Optional, Tuple
import inspect
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.constants import Endian
#from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.client.mixin import ModbusClientMixin

from .const import BETRIEBSART_MODI, BETRIEBSART_HK, KAELTEKREIS_MODI, PUPU_MODI, PV_UEBERSCHUSSREGELUNG, SGREADY_MODUS, SOLLWERTANHEBUNG_PVPLUS, WP_STATUS

_LOGGER = logging.getLogger(__name__)

class OvumModbusHub(DataUpdateCoordinator[Dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, name: str, host: str, port: int, slave: int, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=scan_interval),
            update_method=self._async_update_data,
        )
        self._host = host
        self._port = port
        self._slave = slave
        self._client: Optional[AsyncModbusTcpClient] = None
        self._read_lock = asyncio.Lock()
        self._connection_lock = asyncio.Lock()
        self.updating_settings = False
        self.firmware_data: Dict[str, Any] = {}
        self._closing = False
        self._reconnecting = False
        self._max_retries = 2
        self._retry_delay = 1
        self._operation_timeout = 30

    def _create_client(self) -> AsyncModbusTcpClient:
        """Creates a new optimized instance of the AsyncModbusTcpClient."""
        client = AsyncModbusTcpClient(
            host=self._host,
            port=self._port,
            timeout=10,
        )
        _LOGGER.debug(f"Created new Modbus client: AsyncModbusTcpClient {self._host}:{self._port}.")
        return client

    async def update_connection_settings(self, host: str, port: int, slave: int, scan_interval: int) -> None:
        """Updates the connection settings with improved synchronization."""
        async with self._connection_lock:
            self.updating_settings = True
            try:
                connection_changed = (host != self._host) or (port != self._port) or (slave != self._slave)
                self._host = host
                self._port = port
                self._slave = slave
                self.update_interval = timedelta(seconds=scan_interval)

                if connection_changed:
                    await self._safe_close()
                    self._client = self._create_client()
                    await self.ensure_connection()
            finally:
                self.updating_settings = False

    async def _safe_close(self) -> bool:
        """Safely closes the Modbus connection."""
        if not self._client:
            return True

        try:
            if self._client.connected:
                close = getattr(self._client, "close", None)
                if close:
                    await close() if inspect.iscoroutinefunction(close) else close()
                transport = getattr(self._client, "transport", None)
                if transport:
                    transport.close()
                await asyncio.sleep(0.2)
                return not self._client.connected
            return True
        except Exception as e:
            _LOGGER.warning(f"Error during safe close: {e}", exc_info=True)
            return False
        finally:
            self._client = None


    async def close(self) -> None:
        """Closes the Modbus connection with improved resource management."""
        if self._closing:
            return

        self._closing = True
        try:
            async with asyncio.timeout(5.0):
                async with self._connection_lock:
                    await self._safe_close()
        except (asyncio.TimeoutError, Exception) as e:
            _LOGGER.warning(f"Error during close: {e}", exc_info=True)
        finally:
            self._closing = False


    async def ensure_connection(self) -> bool:
        """Ensure the Modbus connection is established and stable."""
        if self._client and self._client.connected:
            return True

        self._client = self._client or self._create_client()
        try:
            await asyncio.wait_for(self._client.connect(), timeout=10)
            _LOGGER.info("Successfully connected to Modbus server.")
        except Exception as e:
            _LOGGER.warning(f"Error during connection attempt: {e}", exc_info=True)
            raise ConnectionException("Failed to connect to Modbus server.") from e

    async def try_read_registers(
        self,
        unit: int,
        address: int,
        count: int,
        max_retries: int = 3,
        base_delay: float = 2.0
    ) -> List[int]:
        """Reads Modbus registers with optimized error handling."""
        for attempt in range(max_retries):
            try:
                async with self._read_lock:
                    response = await self._client.read_holding_registers(address=address, count=count, slave=self._slave)

                if (not response)  or response.isError() or len(response.registers) != count:
                    raise ModbusIOException(f"Invalid response from address {address}")

                return response.registers

            except (ModbusIOException, ConnectionException) as e:
                _LOGGER.error(f"Read attempt {attempt + 1} failed at address {address}: {e}")
                if attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt), 10.0)
                    await asyncio.sleep(delay)
                    if not await self._safe_close():
                        _LOGGER.warning("Failed to safely close the Modbus client.")
                    try:
                        await self.ensure_connection()
                    except ConnectionException:
                        _LOGGER.error("Failed to reconnect Modbus client.")
                        continue
                    else:
                        _LOGGER.info("Reconnected Modbus client successfully.")

        _LOGGER.error(f"Failed to read registers from unit {unit}, address {address} after {max_retries} attempts")
        raise ConnectionException(f"Read operation failed for address {address} after {max_retries} attempts")

    async def _async_update_data(self) -> Dict[str, Any]:
        await self.ensure_connection()
        if not self.firmware_data:
            self.firmware_data.update(await self.read_modbus_firmware_data())
        combined_data = {**self.firmware_data}

        for read_method in [
            self.read_realtime_data_1,
            self.read_realtime_data_2,
            self.read_realtime_data_3,
            self.read_realtime_data_4,
            self.read_realtime_data_5,
            self.read_realtime_data_6,
            self.read_realtime_data_7,
            self.read_realtime_data_8,
            self.read_realtime_data_9,
            self.read_realtime_data_A,
            self.read_realtime_data_B,
            self.read_realtime_data_C,
            self.read_realtime_data_D,
            self.read_realtime_data_E,
            self.read_realtime_data_F,
            self.read_realtime_data_G,
        ]:
            combined_data.update(await read_method())
            await asyncio.sleep(0.2)
        await self.close()
        return combined_data

    async def _read_modbus_data(
        self,
        start_address: int,
        count: int,
        decode_instructions: List[tuple],
        data_key: str,
        default_decoder: str = "decode_16bit_uint",
        default_factor: float = 0.01
    ) -> Dict[str, Any]:
        """
        Reads and decodes Modbus data with optional default decoder and factor.

        Args:
            start_address (int): Starting address for reading registers.
            count (int): Number of registers to read.
            decode_instructions (List[tuple]): Decoding instructions [(key, method, factor)].
            data_key (str): Key for logging or tracking data context.
            default_decoder (str): Default decoding method to use when none is specified.
            default_factor (float): Default factor to apply when none is specified.

        Returns:
            Dict[str, Any]: Decoded data as a dictionary.
        """
        try:
            regs = await self.try_read_registers(self._slave, start_address, count)
            if not regs:
                _LOGGER.error(f"Error reading modbus data: No response for {data_key}")
                return {}

            new_data = {}
            index = 0

            for instruction in decode_instructions:
                key, method, factor = (instruction + (default_factor,))[:3]
                method = method or default_decoder 

                if method == "skip_bytes":
                    index += factor //2 # Each register is 2 bytes long
                    continue

                if not key:
                    continue

                try:
                    raw_value = regs[index]

                    # Selection of the correct decoding method
                    if method == "decode_16bit_int":
                        value = self._client.convert_from_registers([raw_value], ModbusClientMixin.DATATYPE.INT16)
                    elif method == "decode_16bit_uint":
                        value = self._client.convert_from_registers([raw_value], ModbusClientMixin.DATATYPE.UINT16)
                    elif method == "decode_32bit_int":
                        if index + 1 < len(regs):
                            value = self._client.convert_from_registers([raw_value, regs[index + 1]], ModbusClientMixin.DATATYPE.INT32)
                            index += 1  # 32-bit values occupy two registers
                        else:
                            value = 0
                    elif method == "decode_32bit_uint":
                        if index + 1 < len(regs):
                            value = self._client.convert_from_registers([raw_value, regs[index + 1]], ModbusClientMixin.DATATYPE.UINT32)
                            index += 1  # 32-bit values occupy two registers
                        else:
                            value = 0
                    else:
                        value = raw_value  # Default value if no conversion is necessary

                    new_data[key] = round(value * factor, 2) if factor != 1 else value
                    index += 1

                except Exception as e:
                    _LOGGER.error(f"Error decoding {key}: {e}")
                    return {}

            return new_data

        except Exception as e:
            _LOGGER.error(f"Error reading modbus data: {e}")
            return {}


    async def read_modbus_firmware_data(self) -> Dict[str, Any]:
        """Reads basic firmware data."""
        try:
            regs = await self.try_read_registers(self._slave, 0x7, 2)
            data = {}
            index = 0

            # Basic parameters
            if index + 1 < len(regs):
                data["firmware"] = self._client.convert_from_registers([regs[index], regs[index + 1]], ModbusClientMixin.DATATYPE.INT32)
                index += 1 # 32-bit register = 2 bytes

            return data

        except Exception as e:
            _LOGGER.error(f"Error reading firmware data: {e}")
            return {}

    async def read_realtime_data_1(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 29-37."""

        decode_instructions_realtime_data1 = [
            ("pumpe_hk1_num", None),
            (None, "skip_bytes", 4),
            ("kombiausgang_pupu", None),
            (None, "skip_bytes", 2),
            ("stufe2b", None),
            ("kuehlventil", None),
            ("stufe2a", None),
        ]

        data = await self._read_modbus_data(
            29, 8, decode_instructions_realtime_data1, 'realtime_data1',
            default_decoder="decode_16bit_uint", default_factor=1
        )

        data["pumpe_hk1"] = BETRIEBSART_MODI.get(data.get("pumpe_hk1_num"), "Unknown")

        return data


    async def read_realtime_data_2(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 78-88."""

        decode_instructions_realtime_data2 = [
            ("waermeleistung", "decode_16bit_uint", 10),
            (None, "skip_bytes", 18),
            ("betriebsstuden_kompressor", None),
        ]

        return await self._read_modbus_data(
            78, 11, decode_instructions_realtime_data2, 'realtime_data2',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_3(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 103-109."""

        decode_instructions_realtime_data3 = [
            ("waermepumpenaustritt", "decode_16bit_int", 0.1),
            ("waermepumpeneintritt", "decode_16bit_int", 0.1),
            (None, "skip_bytes", 8),
            ("laufzeit_seit_letztem_start", None),
        ]

        return await self._read_modbus_data(
            103, 7, decode_instructions_realtime_data3, 'realtime_data3',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_4(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 199-218."""

        decode_instructions_realtime_data4 = [
            ("betriebsart_warmwasser_num", "decode_16bit_uint", 1),
            ("temperatur_wwspeicher_oben", None),
            ("temperatur_wwspeicher_unten", None),
            ("temperatur_zapf_fws", None),
            ("pumpe_fws_ausgang", "decode_16bit_uint", 0.01),
            (None, "skip_bytes", 22),
            ("temperatur_ww_soll", None),
            (None, "skip_bytes", 4),
            ("temperatur_zapf_soll", None),
        ]

        data = await self._read_modbus_data(
            199, 20, decode_instructions_realtime_data4, 'realtime_data4',
            default_decoder="decode_16bit_int", default_factor=0.1
        )

        data["betriebsart_warmwasser"] = BETRIEBSART_MODI.get(data.get("betriebsart_warmwasser_num"), "Unknown")

        return data

    async def read_realtime_data_5(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 249."""

        decode_instructions_realtime_data5 = [
            ("status_kombiausgang_pupu_num", None),
        ]

        data = await self._read_modbus_data(
            249, 1, decode_instructions_realtime_data5, 'realtime_data5',
            default_decoder="decode_16bit_uint", default_factor=1
        )

        data["status_kombiausgang_pupu"] = BETRIEBSART_MODI.get(data.get("status_kombiausgang_pupu_num"), "Unknown")

        return data

    async def read_realtime_data_6(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 352-355."""

        decode_instructions_realtime_data6 = [
            ("anzahl_aktive_alarme", None),
            (None, "skip_bytes", 4),
            ("max_neustarts_erreicht", None),
        ]

        return await self._read_modbus_data(
            352, 4, decode_instructions_realtime_data6, 'realtime_data6',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_7(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 449-455."""

        decode_instructions_realtime_data7 = [
            ("autarkiegrad_ueberschussbetrieb", None),
            (None, "skip_bytes", 10),
            ("pv_watch_messwert", "decode_16bit_int", 10),
        ]

        return await self._read_modbus_data(
            449, 7, decode_instructions_realtime_data7, 'realtime_data7',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_8(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 499-523."""

        decode_instructions_realtime_data8 = [
            ("betriebsart_heizung_num", "decode_16bit_uint", 1),
            (None, "skip_bytes", 4),
            ("vorlauftemperatur_hk1", None),
            ("ruecklauftemperatur_hk1", None),
            ("temperatur_speicher", None),
            ("aussentemperatur_gemittelt", None),
            (None, "skip_bytes", 34),
            ("raumsolltemperatur_hk1", None),
        ]

        data = await self._read_modbus_data(
            499, 25, decode_instructions_realtime_data8, 'realtime_data8',
            default_decoder="decode_16bit_int", default_factor=0.1
        )

        data["betriebsart_heizung"] = BETRIEBSART_MODI.get(data.get("betriebsart_heizung_num"), "Unknown")

        return data

    async def read_realtime_data_9(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 531-554."""

        decode_instructions_realtime_data9 = [
            ("kombiausgang_pupu_modi_num", "decode_16bit_uint", 1),
            (None, "skip_bytes", 4),
            ("vorlauftemperatur_hk2", None),
            ("vorlaufsolltemperatur_hk2", None),
            ("raumsolltemperatur_hk2", None),
            (None, "skip_bytes", 36),
            ("vorlaufsolltemperatur_hk1", None),
        ]

        data = await self._read_modbus_data(
            531, 25, decode_instructions_realtime_data9, 'realtime_data9',
            default_decoder="decode_16bit_int", default_factor=0.1
        )

        data["kombiausgang_pupu_modi"] = PUPU_MODI.get(data.get("kombiausgang_pupu_modi_num"), "Unknown")

        return data

    async def read_realtime_data_A(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 640-641."""

        decode_instructions_realtime_dataA = [
            ("betriebsart_hk1_num", None),
            ("betriebsart_hk2_num", None),
        ]

        data = await self._read_modbus_data(
            640, 2, decode_instructions_realtime_dataA, 'realtime_dataA',
            default_decoder="decode_16bit_uint", default_factor=1
        )

        data["betriebsart_hk1"] = BETRIEBSART_HK.get(data.get("betriebsart_hk1_num"), "Unknown")
        data["betriebsart_hk2"] = BETRIEBSART_HK.get(data.get("betriebsart_hk2_num"), "Unknown")

        return data

    async def read_realtime_data_B(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 699-710."""

        decode_instructions_realtime_dataB = [
            ("speichersolltemperatur_pvplus_betrieb", "decode_16bit_uint", 0.1),
            (None, "skip_bytes", 4),
            ("sollwertanhebung_ww_pvplus", None),
            ("sollwertanhebung_heizung_pvplus_num", None),
            (None, "skip_bytes", 6),
            ("el_leistung_wp", "decode_16bit_uint", 10),
            ("pvplus_regelungsart_num", None),
            ("sollwert_pvwatch_tcp", "decode_16bit_int", 10),
            ("sollwert_leistungsaufnahme_tcp", "decode_16bit_uint", 10),
        ]

        data = await self._read_modbus_data(
            699, 12, decode_instructions_realtime_dataB, 'realtime_dataB',
            default_decoder="decode_16bit_uint", default_factor=1
        )

        data["sollwertanhebung_heizung_pvplus"] = SOLLWERTANHEBUNG_PVPLUS.get(data.get("sollwertanhebung_heizung_pvplus_num"), "Unknown")
        data["pvplus_regelungsart"] = PV_UEBERSCHUSSREGELUNG.get(data.get("pvplus_regelungsart_num"), "Unknown")

        return data

    async def read_realtime_data_C(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 749."""

        decode_instructions_realtime_dataC = [
            ("pv_anforderung_aktiv", None),
        ]

        return await self._read_modbus_data(
            749, 1, decode_instructions_realtime_dataC, 'realtime_dataC',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_D(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 1149."""

        decode_instructions_realtime_dataD = [
            ("abtaustatus", None),
        ]

        return await self._read_modbus_data(
            1149, 1, decode_instructions_realtime_dataD, 'realtime_dataD',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_E(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 1204."""

        decode_instructions_realtime_dataE = [
            ("anforderungsart_kaeltekreis_num", None),
        ]

        data = await self._read_modbus_data(
            1204, 1, decode_instructions_realtime_dataE, 'realtime_dataE',
            default_decoder="decode_16bit_uint", default_factor=1
        )

        data["anforderungsart_kaeltekreis"] = KAELTEKREIS_MODI.get(data.get("anforderungsart_kaeltekreis_num"), "Unknown")

        return data

    async def read_realtime_data_F(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 1249-1251."""

        decode_instructions_realtime_dataF = [
            ("sg_ready_modus_num", None),
            ("sg_ready_kontakt1", None),
            ("sg_ready_kontakt2", None),
        ]

        data = await self._read_modbus_data(
            1249, 3, decode_instructions_realtime_dataF, 'realtime_dataF',
            default_decoder="decode_16bit_uint", default_factor=1
        )

        data["sg_ready_modus"] = SGREADY_MODUS.get(data.get("sg_ready_modus_num"), "Unknown")

        return data

    async def read_realtime_data_G(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 1999."""

        decode_instructions_realtime_dataG = [
            ("wp_status_num", None),
        ]

        data = await self._read_modbus_data(
            1999, 1, decode_instructions_realtime_dataG, 'realtime_dataG',
            default_decoder="decode_16bit_uint", default_factor=1
        )

        data["wp_status"] = WP_STATUS.get(data.get("wp_status_num"), "Unknown")

        return data

