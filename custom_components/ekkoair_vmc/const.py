"""Constants for the EkkoAir VMC integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "ekkoair_vmc"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.NUMBER]

CONF_TRANSPORT = "transport"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_DEVICE = "device"
CONF_BAUDRATE = "baudrate"
CONF_BYTESIZE = "bytesize"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"
CONF_UNIT_ID = "unit_id"
CONF_SCAN_INTERVAL = "scan_interval"

TRANSPORT_TCP = "tcp"
TRANSPORT_SERIAL = "serial"

# These are protocol addresses from the EkkoAir Modbus manual.
REG_PANEL_FRONT = 0x9C40
REG_ACT_STATE_1 = 0x7531
REG_ACT_T_ROOM = 0x7540
REG_ACT_T_EXHAUST = 0x7541
REG_FAN1_ACT_AO = 0x7542
REG_FAN1_ACT_TACHO = 0x7543
REG_FAN2_ACT_AO = 0x7544
REG_FAN2_ACT_TACHO = 0x7545

DEFAULT_SCAN_INTERVAL = timedelta(seconds=5)
