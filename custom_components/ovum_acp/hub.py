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
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.exceptions import ConnectionException, ModbusIOException

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
        # self.last_valid_data wurde entfernt
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
            slave=self._slave,
            timeout=10,
            retries=self._max_retries,
            retry_on_empty=True,
            close_comm_on_error=False,
            strict=False
        )
        _LOGGER.debug(f"Created new Modbus client: AsyncModbusTcpClient {self._host}:{self._port}, slave {self._slave}")
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

        try:
                self._client = self._client or self._create_client()
                if await asyncio.wait_for(self._client.connect(), timeout=10):
                        _LOGGER.info("Successfully connected to Modbus server.")
                        return True
                _LOGGER.warning("Failed to connect to Modbus server.")
        except Exception as e:
                _LOGGER.warning(f"Error during connection attempt: {e}", exc_info=True)

        return False

    async def try_read_registers(
        self,
        address: int,
        count: int,
        max_retries: int = 3,
        base_delay: float = 2.0
    ) -> List[int]:
        """Reads Modbus registers with optimized error handling and on-demand connection check."""
        start_time = time.time()

        for attempt in range(max_retries):
                try:
                        # Establish connection only if needed
                        if not self._client or not await self.ensure_connection():
                                raise ConnectionException("Unable to establish connection")

                        # Read attempt with Modbus client
                        async with self._read_lock:
                                response = await self._client.read_holding_registers(address, count, slave=self._slave)

                        # Check the response and number of registers
                        if not isinstance(response, ReadHoldingRegistersResponse) or response.isError() or len(response.registers) != count:
                                raise ModbusIOException(f"Invalid response from address {address}")

                        #_LOGGER.info(f"Successfully read registers at address {address}.")
                        return response.registers

                except (ModbusIOException, ConnectionException) as e:
                        _LOGGER.error(f"Read attempt {attempt + 1} failed at address {address}: {e}")

                        # Exponential backoff for retry
                        if attempt < max_retries - 1:
                                await asyncio.sleep(min(base_delay * (2 ** attempt), 10.0))

                                # In case of connection problems, safely close the current connection and rebuild it
                                if not await self._safe_close():
                                        _LOGGER.warning("Failed to safely close the Modbus client.")
                                        
                                # Ensure reconnection
                                if not await self.ensure_connection():
                                        _LOGGER.error("Failed to reconnect Modbus client.")
                                else:
                                        _LOGGER.info("Reconnected Modbus client successfully.")

        # If all attempts failed
        _LOGGER.error(f"Failed to read registers from slave {self._slave}, address {address} after {max_retries} attempts")
        raise ConnectionException(f"Read operation failed for address {address} after {max_retries} attempts")

    async def _async_update_data(self) -> Dict[str, Any]:
        """Updates all data records."""
        if not self.firmware_data:
                self.firmware_data.update(await self.read_modbus_firmware_data())

        data_read_methods = [
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
        ]

        combined_data = {**self.firmware_data}

        for read_method in data_read_methods:
                combined_data.update(await read_method())
                await asyncio.sleep(0.2)  # 200ms pause between read operations

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
            regs = await self.try_read_registers(start_address, count)
            decoder = BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG)
            new_data: Dict[str, Any] = {}

            for instruction in decode_instructions:
                try:
                    key, method, factor = instruction if len(instruction) == 3 else (*instruction, default_factor)
                    method = method or default_decoder  # Use default decoder if none is specified

                    if method == "skip_bytes":
                        decoder.skip_bytes(factor)
                        continue

                    if not key:
                        continue

                    value = getattr(decoder, method)()
                    if isinstance(value, bytes):
                        value = value.decode("ascii", errors="replace").strip()
                    
                    new_data[key] = round(value * factor, 2) if factor != 1 else value

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
            regs = await self.try_read_registers(0x7, 2)
            decoder = BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG)
            data = {}

            # Basic parameters
            data["firmware"] = decoder.decode_32bit_int()

            return data

        except Exception as e:
            _LOGGER.error(f"Error reading firmware data: {e}")
            return {}

    async def read_realtime_data_1(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 29-37."""

        decode_instructions_realtime_data1 = [
            ("pumpe_hk1", None),
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

        return data


    async def read_realtime_data_2(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 78-88."""

        decode_instructions_realtime_data2 = [
            ("waermeleistung", "decode_16bit_uint", 0.01),
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
            ("betriebsart_warmwasser", None),
            ("temperatur_wwspeicher_oben", None),
            ("temperatur_wwspeicher_unten", None),
            (None, "skip_bytes", 2),
            ("temperatur_zapf_fws", None),
            (None, "skip_bytes", 22),
            ("temperatur_ww_soll", None),
            (None, "skip_bytes", 4),
            ("temperatur_zapf_soll", None),
        ]

        return await self._read_modbus_data(
            199, 20, decode_instructions_realtime_data4, 'realtime_data4',
            default_decoder="decode_16bit_int", default_factor=0.1
        )

    async def read_realtime_data_5(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 249."""

        decode_instructions_realtime_data5 = [
            ("status_kombiausgang_pupu", None),
        ]

        return await self._read_modbus_data(
            249, 1, decode_instructions_realtime_data5, 'realtime_data5',
            default_decoder="decode_16bit_uint", default_factor=1
        )

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
            ("pv_watch_messwert", "decode_16bit_int", 0.01),
        ]

        return await self._read_modbus_data(
            449, 7, decode_instructions_realtime_data7, 'realtime_data7',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_8(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 499-523."""

        decode_instructions_realtime_data8 = [
            ("betriebsart_heizung", "decode_16bit_uint", 1),
            (None, "skip_bytes", 4),
            ("vorlauftemperatur_hk1", None),
            ("ruecklauftemperatur_hk1", None),
            ("temperatur_speicher", None),
            ("aussentemperatur_gemittelt", None),
            (None, "skip_bytes", 34),
            ("raumsolltemperatur_hk1", None),
        ]

        return await self._read_modbus_data(
            499, 25, decode_instructions_realtime_data8, 'realtime_data8',
            default_decoder="decode_16bit_int", default_factor=0.1
        )

    async def read_realtime_data_9(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 531-554."""

        decode_instructions_realtime_data9 = [
            ("kombiausgang_pupu_modi", "decode_16bit_uint", 1),
            (None, "skip_bytes", 4),
            ("vorlauftemperatur_hk2", None),
            ("vorlaufsolltemperatur_hk2", None),
            ("raumsolltemperatur_hk2", None),
            (None, "skip_bytes", 36),
            ("vorlaufsolltemperatur_hk1", None),
        ]

        return await self._read_modbus_data(
            531, 24, decode_instructions_realtime_data9, 'realtime_data9',
            default_decoder="decode_16bit_int", default_factor=0.1
        )

    async def read_realtime_data_A(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 640-641."""

        decode_instructions_realtime_dataA = [
            ("betriebsart_hk1", None),
            ("betriebsart_hk1", None),
        ]

        return await self._read_modbus_data(
            640, 2, decode_instructions_realtime_dataA, 'realtime_dataA',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_B(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 699-710."""

        decode_instructions_realtime_dataB = [
            ("speichersolltemperatur_pvplus_betrieb", "decode_16bit_uint", 0.1),
            (None, "skip_bytes", 4),
            ("sollwertanhebung_ww_pvplus", None),
            ("sollwertanhebung_heizung_pvplus", None),
            (None, "skip_bytes", 6),
            ("el_leistung_wp", "decode_16bit_uint", 0.01),
            ("pvplus_regelungsart", None),
            ("sollwert_pvwatch_tcp", "decode_16bit_int", 0.01),
            ("sollwert_leistungsaufnahme_tcp", "decode_16bit_uint", 0.01),
        ]

        return await self._read_modbus_data(
            699, 12, decode_instructions_realtime_dataB, 'realtime_dataB',
            default_decoder="decode_16bit_uint", default_factor=1
        )

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
            ("anforderungsart_kaeltekreis", None),
        ]

        return await self._read_modbus_data(
            1204, 1, decode_instructions_realtime_dataE, 'realtime_dataE',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_F(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 1249-1251."""

        decode_instructions_realtime_dataF = [
            ("sg_ready_modus", None),
            ("sg_ready_kontakt1", None),
            ("sg_ready_kontakt2", None),
        ]

        return await self._read_modbus_data(
            1249, 3, decode_instructions_realtime_dataF, 'realtime_dataF',
            default_decoder="decode_16bit_uint", default_factor=1
        )

    async def read_realtime_data_G(self) -> Dict[str, Any]:
        """Reads real-time operating data, Modbus 1999."""

        decode_instructions_realtime_dataG = [
            ("wp_status", None),
        ]

        return await self._read_modbus_data(
            1999, 1, decode_instructions_realtime_dataG, 'realtime_dataG',
            default_decoder="decode_16bit_uint", default_factor=1
        )

