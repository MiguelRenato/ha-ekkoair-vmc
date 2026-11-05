"""Fan level control for EkkoAir VMC."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VmcConfigEntry
from .const import REG_PANEL_FRONT
from .coordinator import VmcCoordinator
from .entity import EkkoAirVmcEntity


class EkkoAirVmcFanLevel(EkkoAirVmcEntity, NumberEntity):
    """Set the selected fan speed level (0–7) in the panel register."""

    _attr_name = "Fan Speed Level"
    _attr_icon = "mdi:fan-speed-3"
    _attr_native_min_value = 0
    _attr_native_max_value = 7
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: VmcCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.unique_id}_fan_speed_level"

    @property
    def native_value(self) -> int | None:
        """Return the currently selected level when it is a supported value."""
        level = (self.coordinator.data["panel"] >> 6) & 0x0F
        return level if 0 <= level <= 7 else None

    async def async_set_native_value(self, value: float) -> None:
        """Write bits 6–9 while preserving power, mode, and other panel flags."""
        level = int(value)
        if value != level or not 0 <= level <= 7:
            raise HomeAssistantError("Fan speed level must be a whole number from 0 to 7")

        current = (await self.coordinator.unit.read_holding_registers(REG_PANEL_FRONT, 1))[0]
        value_mask = 0x0F << 6
        updated = (current & ~value_mask) | (level << 6)
        # FC16 is the write function documented for the panel register.
        await self.coordinator.unit.write_registers(REG_PANEL_FRONT, [updated])
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VmcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan speed slider."""
    coordinator: VmcCoordinator = entry.runtime_data
    async_add_entities([EkkoAirVmcFanLevel(coordinator)])
