![EkkoAir](ekkoair_logo_azul.png)

# EkkoAir VMC Home Assistant integration

This custom integration creates an **EkkoAir VMC** device in Home Assistant and groups its entities on the device page.

## Install

1. Copy the `ekkoair_vmc` folder into `/config/custom_components/` so the final path is `/config/custom_components/ekkoair_vmc/`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and search for **EkkoAir VMC**.
4. Choose Modbus TCP or RS-485 / Modbus RTU and enter the connection settings. The manual defaults are unit ID `1` and, for RTU, `19200`, `8` data bits, even parity, `1` stop bit.

The TCP connection needs the gateway's Modbus port. A Node-RED editor address such as `http://HOST:1880` is not a Modbus endpoint. For a transparent RTU serial server, use a device value such as `socket://HOST:PORT` in the serial option. For native Modbus TCP gateways, use the TCP option.

## Entities

- VMC power, Summer Mode, Boost Mode, and Touch Button Lock switches, each preserving the other bits in holding register `0x9C40` and writing via FC16.
- Fan speed level slider (0–7), writing only bits 6–9 of holding register `0x9C40` and preserving the other panel settings.
- Power, fan-active, Summer Mode, Boost, Touch Button Lock, and fan tachometer binary sensors.
- Interface and fan operating states, room and exhaust temperatures, fan output voltages, fan level, temperature level, AQS mode, tachometer timers, and sensor status.

The slider sets the selected fan level; it is not an RPM control. Fan voltages are reported in volts; the manual does not provide motor RPM or the physical bypass damper position. Summer Mode and Boost controls may be ignored by the VMC when its activation conditions are not met. The EkkoAir logo and square integration icon use a pale background for contrast on dark themes. Home Assistant 2026.3 and newer can display these local brand assets in its interface.

Temperature sensor status entities report text: `OK`, `Sensor disconnected`, `Sensor short circuit`, or `Undefined (not documented)` for status code 3.

## Notes

The integration uses Home Assistant's shared Modbus connection and PyModbus backend. Do not configure Node-RED and Home Assistant as simultaneous masters on the same RS-485 bus; the device manual specifies one master per bus.
