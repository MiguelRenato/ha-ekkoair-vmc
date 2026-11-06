"""Poll and decode EkkoAir VMC Modbus registers."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection import ModbusError, ModbusUnit

from .const import (
    DOMAIN,
    REG_ACT_STATE_1,
    REG_ACT_T_EXHAUST,
    REG_ACT_T_ROOM,
    REG_BOOST_DURATION,
    REG_FAN1_ACT_AO,
    REG_FAN1_ACT_TACHO,
    REG_FAN2_ACT_AO,
    REG_FAN2_ACT_TACHO,
    REG_PANEL_FRONT,
)


def decode_temperature(raw: int) -> tuple[float | None, int]:
    """Decode the 14-bit signed temperature and the two sensor-status bits."""
    sensor_status = (raw >> 14) & 0x03
    temperature = raw & 0x3FFF
    if temperature & 0x2000:
        temperature -= 0x4000
    value = round(temperature / 10, 1) if sensor_status == 0 else None
    return value, sensor_status


class VmcCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Read the VMC registers using Home Assistant's shared Modbus link."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        unit: ModbusUnit,
        *,
        scan_interval: int,
    ) -> None:
        self.entry = entry
        self.unit = unit
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Read only small contiguous blocks; the device caps reads at 13 registers."""
        try:
            panel = (await self.unit.read_holding_registers(REG_PANEL_FRONT, 1))[0]
            boost_duration = (await self.unit.read_holding_registers(REG_BOOST_DURATION, 1))[0]
            act_state_1 = (await self.unit.read_input_registers(REG_ACT_STATE_1, 1))[0]
            registers = await self.unit.read_input_registers(REG_ACT_T_ROOM, 6)
        except (ModbusError, IndexError) as err:
            raise UpdateFailed(f"Unable to read EkkoAir VMC registers: {err}") from err

        room_temp, room_sensor_status = decode_temperature(registers[0])
        exhaust_temp, exhaust_sensor_status = decode_temperature(registers[1])
        return {
            "panel": panel,
            "boost_duration": boost_duration,
            "act_state_1": act_state_1,
            "room_temperature": room_temp,
            "room_sensor_status": room_sensor_status,
            "exhaust_temperature": exhaust_temp,
            "exhaust_sensor_status": exhaust_sensor_status,
            "fan1_voltage": registers[2] / 100,
            "fan1_tacho": registers[3],
            "fan2_voltage": registers[4] / 100,
            "fan2_tacho": registers[5],
        }
