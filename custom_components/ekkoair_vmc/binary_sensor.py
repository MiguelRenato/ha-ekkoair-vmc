"""Binary sensors for EkkoAir VMC."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VmcConfigEntry
from .coordinator import VmcCoordinator
from .entity import EkkoAirVmcEntity

IsOnFn = Callable[[dict[str, Any]], bool]


@dataclass(frozen=True, kw_only=True)
class VmcBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a VMC boolean value."""

    is_on_fn: IsOnFn


BINARY_SENSORS: tuple[VmcBinarySensorDescription, ...] = (
    VmcBinarySensorDescription(
        key="power",
        name="Power",
        device_class=BinarySensorDeviceClass.POWER,
        is_on_fn=lambda data: bool(data["panel"] & 0x0001),
    ),
    VmcBinarySensorDescription(
        key="fans_active",
        name="Fans Active",
        is_on_fn=lambda data: ((data["act_state_1"] >> 8) & 0x0F) in (4, 5, 8, 9),
    ),
    VmcBinarySensorDescription(
        key="summer_mode",
        name="Summer Mode Status",
        is_on_fn=lambda data: bool((data["panel"] >> 2) & 1),
    ),
    VmcBinarySensorDescription(
        key="summer_auto_off_flag",
        name="Summer Auto-Off Flag",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: bool((data["panel"] >> 3) & 1),
    ),
    VmcBinarySensorDescription(
        key="boost_mode",
        name="Boost Mode Status",
        is_on_fn=lambda data: bool((data["panel"] >> 4) & 1),
    ),
    VmcBinarySensorDescription(
        key="touch_lock",
        name="Touch Button Lock Status",
        is_on_fn=lambda data: bool((data["panel"] >> 5) & 1),
    ),
    VmcBinarySensorDescription(
        key="fan1_tacho_signal",
        name="Fan 1 Tacho Signal",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: bool(data["fan1_tacho"] & 1),
    ),
    VmcBinarySensorDescription(
        key="fan1_startup_successful",
        name="Fan 1 Startup Successful",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: bool((data["fan1_tacho"] >> 1) & 1),
    ),
    VmcBinarySensorDescription(
        key="fan2_tacho_signal",
        name="Fan 2 Tacho Signal",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: bool(data["fan2_tacho"] & 1),
    ),
    VmcBinarySensorDescription(
        key="fan2_startup_successful",
        name="Fan 2 Startup Successful",
        entity_category="diagnostic",
        is_on_fn=lambda data: bool((data["fan2_tacho"] >> 1) & 1),
    ),
)


class EkkoAirVmcBinarySensor(EkkoAirVmcEntity, BinarySensorEntity):
    """A binary sensor backed by a VMC register bit field."""

    entity_description: VmcBinarySensorDescription

    def __init__(
        self,
        coordinator: VmcCoordinator,
        description: VmcBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.unique_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return the current state."""
        return self.entity_description.is_on_fn(self.coordinator.data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VmcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VMC binary sensors."""
    coordinator: VmcCoordinator = entry.runtime_data
    async_add_entities(
        EkkoAirVmcBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )
