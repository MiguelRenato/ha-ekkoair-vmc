"""Controls for EkkoAir VMC panel settings."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VmcConfigEntry
from .const import REG_PANEL_FRONT
from .coordinator import VmcCoordinator
from .entity import EkkoAirVmcEntity


class EkkoAirVmcPowerSwitch(EkkoAirVmcEntity, SwitchEntity):
    """Switch the VMC by changing only bit 0 of the panel register."""

    _attr_name = "VMC"
    _attr_icon = "mdi:hvac"

    def __init__(self, coordinator: VmcCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.unique_id}_power_switch"

    @property
    def is_on(self) -> bool:
        """Return the power flag from the latest panel register read."""
        return bool(self.coordinator.data["panel"] & 0x0001)

    async def async_turn_on(self, **kwargs) -> None:
        """Set the power flag without disturbing other panel settings."""
        await self._async_set_power(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Clear the power flag without disturbing other panel settings."""
        await self._async_set_power(False)

    async def _async_set_power(self, turn_on: bool) -> None:
        current = (await self.coordinator.unit.read_holding_registers(REG_PANEL_FRONT, 1))[0]
        value = current | 0x0001 if turn_on else current & 0xFFFE
        # The manual documents FC16 for writing holding registers.
        await self.coordinator.unit.write_registers(REG_PANEL_FRONT, [value])
        await self.coordinator.async_request_refresh()


class EkkoAirVmcPanelBitSwitch(EkkoAirVmcEntity, SwitchEntity):
    """Switch one writable panel flag while preserving all other register bits."""

    def __init__(
        self,
        coordinator: VmcCoordinator,
        *,
        key: str,
        name: str,
        bit: int,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._bit_mask = 1 << bit
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.entry.unique_id}_{key}_switch"

    @property
    def is_on(self) -> bool:
        """Return the selected panel flag from the latest register poll."""
        return bool(self.coordinator.data["panel"] & self._bit_mask)

    async def async_turn_on(self, **kwargs) -> None:
        """Set only this panel flag."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Clear only this panel flag."""
        await self._async_set_state(False)

    async def _async_set_state(self, enabled: bool) -> None:
        current = (await self.coordinator.unit.read_holding_registers(REG_PANEL_FRONT, 1))[0]
        value = current | self._bit_mask if enabled else current & ~self._bit_mask
        # The manual documents FC16 for writing holding registers.
        await self.coordinator.unit.write_registers(REG_PANEL_FRONT, [value])
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VmcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the VMC switches."""
    coordinator: VmcCoordinator = entry.runtime_data
    async_add_entities(
        [
            EkkoAirVmcPowerSwitch(coordinator),
            EkkoAirVmcPanelBitSwitch(
                coordinator,
                key="summer_mode",
                name="Summer Mode",
                bit=2,
                icon="mdi:sun-snowflake-variant",
            ),
            EkkoAirVmcPanelBitSwitch(
                coordinator,
                key="boost_mode",
                name="Boost Mode",
                bit=4,
                icon="mdi:fan-plus",
            ),
            EkkoAirVmcPanelBitSwitch(
                coordinator,
                key="touch_lock",
                name="Touch Button Lock",
                bit=5,
                icon="mdi:lock",
            ),
        ]
    )
