"""EkkoAir VMC custom integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.modbus import async_get_unit
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_DEVICE,
    CONF_HOST,
    CONF_PARITY,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_STOPBITS,
    CONF_TRANSPORT,
    CONF_UNIT_ID,
    DOMAIN,
    PLATFORMS,
    TRANSPORT_SERIAL,
)
from .coordinator import VmcCoordinator

if TYPE_CHECKING:
    from modbus_connection import ModbusSerialParams, ModbusTcpParams

    VmcConfigEntry = ConfigEntry[VmcCoordinator]
else:
    VmcConfigEntry = ConfigEntry


def make_connection_params(data: dict[str, object]) -> ModbusTcpParams | ModbusSerialParams:
    """Build the shared Home Assistant Modbus connection parameters."""
    from modbus_connection import ModbusSerialParams, ModbusTcpParams

    if data[CONF_TRANSPORT] == TRANSPORT_SERIAL:
        return ModbusSerialParams(
            device=str(data[CONF_DEVICE]),
            framer="rtu",
            baudrate=int(data[CONF_BAUDRATE]),
            bytesize=int(data[CONF_BYTESIZE]),
            parity=str(data[CONF_PARITY]),
            stopbits=int(data[CONF_STOPBITS]),
        )
    return ModbusTcpParams(host=str(data[CONF_HOST]), port=int(data[CONF_PORT]))


async def async_setup_entry(hass: HomeAssistant, entry: VmcConfigEntry) -> bool:
    """Set up the VMC from a config entry."""
    params = make_connection_params(entry.data)
    unit = async_get_unit(hass, entry, params, int(entry.data[CONF_UNIT_ID]))
    # The manual asks for a short quiet interval between RTU frames. The shared
    # Modbus connection serializes calls from this and other Home Assistant integrations.
    unit.set_message_spacing(0.004)

    coordinator = VmcCoordinator(
        hass,
        entry,
        unit,
        scan_interval=int(entry.data[CONF_SCAN_INTERVAL]),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VmcConfigEntry) -> bool:
    """Unload the VMC platforms."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
