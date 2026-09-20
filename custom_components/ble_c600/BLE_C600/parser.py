"""Parser for C600 BLE devices"""

from __future__ import annotations

import asyncio
import dataclasses
import struct
from collections import namedtuple
from datetime import datetime
import logging

# from logging import Logger
from math import exp
from typing import Any, Callable, Tuple

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import (
    BATT_100, BATT_0
)


READ_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"

# Preserve the original parser's minimum (it accesses byte 17).
# ORP needs bytes 20 and 21 and is handled separately when they are absent.
MIN_FRAME_LENGTH = 18
ORP_FRAME_LENGTH = 22
READ_ATTEMPTS = 3
READ_RETRY_DELAY = 1.0
READ_TIMEOUT = 10.0
DISCONNECT_TIMEOUT = 5.0

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class C600Device:
    """Response data with information about the C600 device"""

    hw_version: str = ""
    sw_version: str = ""
    name: str = ""
    identifier: str = ""
    address: str = ""
    sensors: dict[str, str | float | None] = dataclasses.field(
        default_factory=lambda: {}
    )

# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
class C600BluetoothDeviceData:
    """Data for C600 BLE sensors."""

    _event: asyncio.Event | None
    _command_data: bytearray | None

    def __init__(
        self,
        logger: Logger,
    ):
        super().__init__()
        self.logger = logger
        self.logger.debug("In Device Data")
        
    def decode(self, byte_frame : bytes ):

        frame_array = [int(x) for x in byte_frame]
        size = len(frame_array)

        for i in range(size-1, 0 , -1):
            tmp=frame_array[i]
            hibit1=(tmp&0x55)<<1
            lobit1=(tmp&0xAA)>>1
            tmp=frame_array[i-1]
            hibit=(tmp&0x55)<<1
            lobit=(tmp&0xAA)>>1
            frame_array[i]=0xff -(hibit1|lobit)
            frame_array[i-1]= 0xff -(hibit|lobit1)

        return frame_array
    
    def decode_position(self,decodedData,idx):
        if idx < 0 or idx + 2 > len(decodedData):
            raise BleakError(
                f"C600: missing bytes {idx}:{idx + 2} in {len(decodedData)}-byte frame"
            )
        return int.from_bytes(decodedData[idx:idx+2], byteorder="big", signed=True)

    async def _read_frame(self, client: BleakClient) -> bytearray:
        """Retry short responses without inventing measurements or packet offsets."""
        lengths = []
        for attempt in range(READ_ATTEMPTS):
            if attempt:
                await asyncio.sleep(READ_RETRY_DELAY)
            try:
                data = await asyncio.wait_for(
                    client.read_gatt_char(READ_UUID), timeout=READ_TIMEOUT
                )
            except asyncio.TimeoutError as err:
                raise BleakError(
                    f"C600: BLE read timed out after {READ_TIMEOUT:g} seconds"
                ) from err
            lengths.append(len(data))
            if len(data) >= MIN_FRAME_LENGTH:
                return data
            self.logger.debug(
                "C600 short BLE response, attempt %s/%s: %s bytes, raw=%s",
                attempt + 1, READ_ATTEMPTS, len(data), data.hex(),
            )
        raise BleakError(
            f"C600: short BLE response after {READ_ATTEMPTS} reads "
            f"(lengths: {lengths}; expected at least {MIN_FRAME_LENGTH} bytes "
            "for the configured C600 packet layout)"
        )
        
    async def _get_status(self, client: BleakClient, device: C600Device) -> C600Device:
        _LOGGER.debug("Getting Status")
        data = await self._read_frame(client)
        #_LOGGER.debug("Raw BLE bytes: %s", [hex(b) for b in data])  # Optional but helpful

        decodedData = self.decode(data)
        #_LOGGER.debug("Decoded BLE data: %s", decodedData)

        #for i in range(0, len(decodedData) - 1):  # Prevent out-of-bounds
        #    try:
        #        val = self.decode_position(decodedData, i)
        #        _LOGGER.debug("Pos %02d-%02d: %6d (0x%04X)", i, i + 1, val, val & 0xFFFF)
        #    except Exception as e:
        #        _LOGGER.debug("Pos %02d-%02d: decode failed (%s)", i, i + 1, e)
        
        # temp = ((message[13]<<8) + message[14]);
        # ph = ((message[3]<<8) + message[4]);
        # orp = ((message[9]<<8) + message[10]);
        # battery = ((message[15]<<8) + message[16]);
        # ec = ((message[5]<<8) + message[6]);
        # tds = ((message[7]<<8) + message[8]);
        # cloro = ((message[11]<<8) + message[12]);
        # id(ble_c600_temperature_sensor).publish_state(temp/10.0);
        # id(ble_c600_ph_sensor).publish_state(ph/100.0);
        # id(ble_c600_orp_sensor).publish_state(orp);
        # id(ble_c600_battery).publish_state(battery/31.9);
        # id(ble_c600_ec_sensor).publish_state(ec);
        # id(ble_c600_tds_sensor).publish_state(tds);
        # id(ble_c600_cloro).publish_state(cloro/10.0)
        
        constant = decodedData[1]
        product_name_code = decodedData[2]
        hold_reading = decodedData[17] >> 4

        backlight_status = (decodedData[17] & 0x0F) >> 3

        battery = round(100 * (self.decode_position(decodedData,15) - BATT_0) / (BATT_100 - BATT_0))
        battery = min(max(0, battery), 100)
        device.sensors["battery"] = battery

        ec = self.decode_position(decodedData,5)
        device.sensors["EC"] = ec
        device.sensors["salt"] = ec * 0.55
        
        device.sensors["TDS"] = self.decode_position(decodedData,7)
        
        cloro = self.decode_position(decodedData,11)
        if cloro < 0:
          device.sensors["cloro"] = 0
        else:
          device.sensors["cloro"] = cloro / 10.0

        device.sensors["pH"] = self.decode_position(decodedData,3) / 100.0 
		
        if len(decodedData) >= ORP_FRAME_LENGTH:
            device.sensors["ORP"] = self.decode_position(decodedData,20) / 1000.0
        else:
            device.sensors["ORP"] = None
            self.logger.debug(
                "C600: %s-byte response lacks ORP bytes 20:22; ORP unknown, raw=%s",
                len(data), data.hex(),
            )
		
        device.sensors["temperature"] = self.decode_position(decodedData,13) / 10.0
        
        #fcAdjust = 0 
        #device.sensors["freeChlorine"] = round( 0.23 * (1 - fcAdjust) * (14 - ph) ** (1/(400 - orp))*(ph - 4.1) ** ( (orp - 516)/145) + 10.0 ** ( (orp + ph * 70 - 1282 ) / 40 ), 1 );  
        
        _LOGGER.debug("Got Status")
        return device

    
    async def update_device(self, ble_device: BLEDevice) -> C600Device:
        """Connects to the device through BLE and retrieves relevant data"""
        _LOGGER.debug("Update Device")
        if ble_device is None:
            raise BleakError("C600: device is not currently available to Home Assistant Bluetooth")
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        _LOGGER.debug("Got Client")
        #await client.pair()
        device = C600Device()
        _LOGGER.debug("Made Device")
        
        try:
            device = await self._get_status(client, device)
            _LOGGER.debug("got Status")
            device.name = ble_device.address
            device.address = ble_device.address
            return device
        finally:
            # Attempt cleanup on success, parsing errors and task cancellation.
            # A cleanup failure must not replace the original read/parse error.
            try:
                await asyncio.wait_for(client.disconnect(), timeout=DISCONNECT_TIMEOUT)
            except Exception as err:
                self.logger.warning(
                    "C600: failed to disconnect from %s: %s", ble_device.address, err
                )
																	 
