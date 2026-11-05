"""Sensors for EkkoAir VMC."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VmcConfigEntry
from .coordinator import VmcCoordinator
from .entity import EkkoAirVmcEntity

ValueFn = Callable[[dict[str, Any]], int | float | str | None]


@dataclass(frozen=True, kw_only=True)
class VmcSensorDescription(SensorEntityDescription):
    """Describe a value decoded from the latest register poll."""

    value_fn: ValueFn


def _ui_state(data: dict[str, Any]) -> int:
    return data["act_state_1"] & 0x0F


def _fan_state(data: dict[str, Any]) -> int:
    return (data["act_state_1"] >> 8) & 0x0F


def _ui_state_text(data: dict[str, Any]) -> str:
    states = {
        0: "Off",
        1: "Off - cooling cycle",
        2: "Fan 1 error",
        3: "Fan 2 error",
        4: "Room temperature sensor error",
        5: "Frost protection sensor error",
        6: "Touch button lock active",
        7: "Touch button lock transition",
        8: "Showing controller settings",
        9: "Setting fan level",
        10: "Setting temperature level",
        11: "Normal operation",
        12: "Service menu",
        13: "User menu",
    }
    code = _ui_state(data)
    return states.get(code, f"Unknown ({code})")


def _fan_state_text(data: dict[str, Any]) -> str:
    states = {
        0: "Off",
        1: "Off - cooling cycle",
        2: "Fan 1 error",
        3: "Fan 2 error",
        4: "Active",
        5: "Active - frost protection",
        6: "Inactive",
        7: "Inactive - frost protection",
        8: "Summer mode",
        9: "Boost",
    }
    code = _fan_state(data)
    return states.get(code, f"Unknown ({code})")


def _temperature_sensor_status_text(status: int) -> str:
    """Describe temperature-sensor status bits from the Modbus register."""
    states = {
        0: "OK",
        1: "Sensor disconnected",
        2: "Sensor short circuit",
        3: "Undefined (not documented)",
    }
    return states.get(status, f"Unknown ({status})")


SENSORS: tuple[VmcSensorDescription, ...] = (
    VmcSensorDescription(key="interface_state", name="Interface State", value_fn=_ui_state_text),
    VmcSensorDescription(key="fan_operating_state", name="Fan Operating State", value_fn=_fan_state_text),
    VmcSensorDescription(
        key="room_temperature",
        name="Room Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data["room_temperature"],
    ),
    VmcSensorDescription(
        key="exhaust_temperature",
        name="Exhaust Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data["exhaust_temperature"],
    ),
    VmcSensorDescription(
        key="room_sensor_status",
        name="Room Temperature Sensor Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _temperature_sensor_status_text(data["room_sensor_status"]),
    ),
    VmcSensorDescription(
        key="exhaust_sensor_status",
        name="Exhaust Temperature Sensor Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _temperature_sensor_status_text(data["exhaust_sensor_status"]),
    ),
    VmcSensorDescription(
        key="fan1_voltage",
        name="Fan 1 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: data["fan1_voltage"],
    ),
    VmcSensorDescription(
        key="fan2_voltage",
        name="Fan 2 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: data["fan2_voltage"],
    ),
    VmcSensorDescription(
        key="fan1_tacho_error_timer",
        name="Fan 1 Tacho Error Timer",
        native_unit_of_measurement="s",
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: ((data["fan1_tacho"] >> 2) & 0x3FFF) / 100,
    ),
    VmcSensorDescription(
        key="fan2_tacho_error_timer",
        name="Fan 2 Tacho Error Timer",
        native_unit_of_measurement="s",
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: ((data["fan2_tacho"] >> 2) & 0x3FFF) / 100,
    ),
    VmcSensorDescription(
        key="aqs_mode",
        name="AQS Mode",
        value_fn=lambda data: "Automatic" if (data["panel"] >> 1) & 1 else "Manual",
    ),
    VmcSensorDescription(
        key="fan_level",
        name="Selected Fan Level",
        value_fn=lambda data: (data["panel"] >> 6) & 0x0F,
    ),
    VmcSensorDescription(
        key="temperature_level",
        name="Selected Temperature Level",
        value_fn=lambda data: (data["panel"] >> 10) & 0x3F,
    ),
)


class EkkoAirVmcSensor(EkkoAirVmcEntity, SensorEntity):
    """A sensor backed by one decoded VMC value."""

    entity_description: VmcSensorDescription

    def __init__(
        self,
        coordinator: VmcCoordinator,
        description: VmcSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.unique_id}_{description.key}"

    @property
    def native_value(self) -> int | float | str | None:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VmcConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VMC sensors."""
    coordinator: VmcCoordinator = entry.runtime_data
    async_add_entities(EkkoAirVmcSensor(coordinator, description) for description in SENSORS)
