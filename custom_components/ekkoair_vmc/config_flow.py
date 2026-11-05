"""Config flow for EkkoAir VMC."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from modbus_connection import ModbusError

from . import make_connection_params
from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_DEVICE,
    CONF_PARITY,
    CONF_SCAN_INTERVAL,
    CONF_STOPBITS,
    CONF_TRANSPORT,
    CONF_UNIT_ID,
    DOMAIN,
    REG_ACT_STATE_1,
    REG_PANEL_FRONT,
    TRANSPORT_SERIAL,
    TRANSPORT_TCP,
)


async def _probe(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Check both register spaces before accepting the connection."""
    params = make_connection_params(data)
    unit_id = int(data[CONF_UNIT_ID])
    async with async_get_temporary_unit(hass, params, unit_id) as unit:
        panel = await unit.read_holding_registers(REG_PANEL_FRONT, 1)
        state = await unit.read_input_registers(REG_ACT_STATE_1, 1)
        if len(panel) != 1 or len(state) != 1:
            raise ModbusError("The VMC returned an incomplete register response")


class EkkoAirVmcConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure the Modbus connection and unit ID."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Select native Modbus TCP or an RTU serial link."""
        if user_input is not None:
            self._transport = user_input[CONF_TRANSPORT]
            if self._transport == TRANSPORT_TCP:
                return await self.async_step_tcp()
            return await self.async_step_serial()

        schema = vol.Schema(
            {
                vol.Required(CONF_TRANSPORT, default=TRANSPORT_TCP): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=TRANSPORT_TCP, label="Modbus TCP gateway"),
                            selector.SelectOptionDict(value=TRANSPORT_SERIAL, label="RS-485 / Modbus RTU"),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_tcp(self, user_input: dict[str, Any] | None = None):
        """Configure a Modbus TCP gateway."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**user_input, CONF_TRANSPORT: TRANSPORT_TCP}
            return await self._async_finish(data, errors)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=502): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                vol.Required(CONF_UNIT_ID, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
                vol.Required(CONF_SCAN_INTERVAL, default=5): vol.All(vol.Coerce(int), vol.Range(min=2, max=300)),
            }
        )
        return self.async_show_form(step_id="tcp", data_schema=schema, errors=errors)

    async def async_step_serial(self, user_input: dict[str, Any] | None = None):
        """Configure local RS-485 or transparent RTU-over-TCP."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**user_input, CONF_TRANSPORT: TRANSPORT_SERIAL}
            return await self._async_finish(data, errors)

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE): str,
                vol.Required(CONF_BAUDRATE, default=19200): vol.All(vol.Coerce(int), vol.Range(min=300, max=115200)),
                vol.Required(CONF_BYTESIZE, default=8): vol.In([7, 8]),
                vol.Required(CONF_PARITY, default="E"): vol.In(["E", "N", "O"]),
                vol.Required(CONF_STOPBITS, default=1): vol.In([1, 2]),
                vol.Required(CONF_UNIT_ID, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
                vol.Required(CONF_SCAN_INTERVAL, default=5): vol.All(vol.Coerce(int), vol.Range(min=2, max=300)),
            }
        )
        return self.async_show_form(
            step_id="serial",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "device_examples": "/dev/serial/by-id/… or socket://192.168.1.20:8899"
            },
        )

    async def _async_finish(self, data: dict[str, Any], errors: dict[str, str]):
        """Probe the device and create the config entry."""
        try:
            params = make_connection_params(data)
            await _probe(self.hass, data)
        except (ModbusError, HomeAssistantError, OSError, ValueError):
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="serial" if data[CONF_TRANSPORT] == TRANSPORT_SERIAL else "tcp",
                data_schema=self._serial_schema() if data[CONF_TRANSPORT] == TRANSPORT_SERIAL else self._tcp_schema(),
                errors=errors,
                description_placeholders={
                    "device_examples": "/dev/serial/by-id/… or socket://192.168.1.20:8899"
                },
            )

        endpoint = ":".join(str(part) for part in params.endpoint)
        await self.async_set_unique_id(f"{endpoint}|{data[CONF_UNIT_ID]}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"EkkoAir VMC ({data[CONF_UNIT_ID]})",
            data=data,
        )

    @staticmethod
    def _tcp_schema() -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=502): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                vol.Required(CONF_UNIT_ID, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
                vol.Required(CONF_SCAN_INTERVAL, default=5): vol.All(vol.Coerce(int), vol.Range(min=2, max=300)),
            }
        )

    @staticmethod
    def _serial_schema() -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_DEVICE): str,
                vol.Required(CONF_BAUDRATE, default=19200): vol.All(vol.Coerce(int), vol.Range(min=300, max=115200)),
                vol.Required(CONF_BYTESIZE, default=8): vol.In([7, 8]),
                vol.Required(CONF_PARITY, default="E"): vol.In(["E", "N", "O"]),
                vol.Required(CONF_STOPBITS, default=1): vol.In([1, 2]),
                vol.Required(CONF_UNIT_ID, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
                vol.Required(CONF_SCAN_INTERVAL, default=5): vol.All(vol.Coerce(int), vol.Range(min=2, max=300)),
            }
        )
