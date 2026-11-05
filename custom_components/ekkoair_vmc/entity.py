"""Base entity for EkkoAir VMC entities."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VmcCoordinator


class EkkoAirVmcEntity(CoordinatorEntity[VmcCoordinator]):
    """Common device association for all VMC entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: VmcCoordinator) -> None:
        super().__init__(coordinator)
        entry_id = coordinator.entry.unique_id or coordinator.entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(entry_id))},
            name="EkkoAir VMC",
            manufacturer="EkkoAir",
            model="Modbus ventilation unit",
        )
