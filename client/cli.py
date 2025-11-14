import asyncio
import time
from asyncio import DatagramTransport

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Iterable, Awaitable

from .utils import generate_sensor_payload
from shared import packet as pkt
from shared.cli.base import BaseCLI
from shared.cli.utils import configure_sensors
from shared.handlers.types import PacketAddr

HELP_MSG = (
    "Available commands:\n"
    "  help / ?                - Show this help message\n"
    "  status / list           - Show sensors status\n"
    "  send <sensor>           - Manually send a packet from sensor\n"
    "  auto <on/off>           - Enable or disable automatic sending\n"
    "  crc <sensor>            - Corrupt the next packet's CRC\n"
    "  check_alive_test <sensor> - Enable the CHECK_ALIVE test mode\n"
    "  configure               - Configure and start sensors\n"
    "  exit / quit             - Stop the client"
)
WELCOME_MSG = "Client CLI started. Type 'configure' to set up and start sensors or 'help' to list commands."


@dataclass
class SensorRuntime:
    identifier: str
    local_ip: str
    local_port: int
    storage: dict


class ClientCLI(BaseCLI):
    def __init__(
        self,
        start_hook: Callable[["ClientCLI", PacketAddr, list[dict]], Awaitable[None]],
        shutdown_callback: Callable[[], None] | Callable[[], asyncio.Future],
    ) -> None:
        self.is_configured = False
        self._start_hook = start_hook
        self._transports: list[DatagramTransport] = []
        self._sensors: list[SensorRuntime] = []

        super().__init__(
            welcome_msg=WELCOME_MSG,
            help_msg=HELP_MSG,
            shutdown_callback=shutdown_callback
        )

    def init(self, *, sensors: Iterable[SensorRuntime], transports: list[DatagramTransport]) -> None:
        self.is_configured = True
        self._sensors = sensors
        self._transports = transports

    async def _handle_command(self, command: str) -> None:
        parts = command.split(" ")
        if not parts:
            return

        cmd, *args = parts
        cmd = cmd.lower()

        if cmd in {"help", "?"}:
            self._print_help()
        elif cmd in {"status", "list"}:
            self._print_status()
        elif cmd == "send":
            await self._command_send(args)
        elif cmd == "auto":
            self._command_auto(args)
        elif cmd == "crc":
            await self._command_crc(args)
        elif cmd == "configure":
            await self._command_configure()
        elif cmd == "check_alive_test":
            await self._command_check_alive(args)
        elif cmd in {"exit", "quit"}:
            await self._shutdown()
        else:
            self.cprint(f"Unknown command: {cmd}. Type 'help' for a list of commands")

    async def _command_configure(self) -> None:
        if self.is_configured:
            self.cprint("Server already configured")
            return

        server_addr, configured_sensors = configure_sensors()
        if not configured_sensors:
            self.cprint("No sensors were configured.")
            return

        await self._start_hook(self, server_addr, configured_sensors)
        count = len(configured_sensors)
        self.cprint(f"Client configured with {count} sensor{'s' if count != 1 else ''}.")

    def _print_status(self) -> None:
        if not self._sensors:
            self.cprint("No sensors configured")
            return

        for idx, sensor in enumerate(self._sensors, start=1):
            storage = sensor.storage
            token = storage.get("token")
            auto_enabled = storage.get("auto_sending", True)
            waiting_ack = storage.get("data_sent_at") is not None and not storage.get("is_data_ack", True)
            check_alive_test = storage.get("check_alive_test")

            self.cprint(
                f"[{idx}] {sensor.identifier}"
                f" | local={sensor.local_ip}:{sensor.local_port}"
                f" | token={'-' if token is None else token}"
                f" | auto={'on' if auto_enabled else 'off'}"
                f" | waiting_ack={'yes' if waiting_ack else 'no'}"
                f" | check_alive_test={'active' if check_alive_test else 'inactive'}"
            )

    def _send_packet(
            self,
            sensor: SensorRuntime,
            payload: dict,
            is_low_battery: bool,
            *,
            force_invalid_crc: bool = False
    ) -> bool:
        storage = sensor.storage
        transport = storage.get("transport")
        if transport is None:
            self.cprint("Transport is not ready yet. Please wait for initialization")
            return False

        token = storage.get("token")
        if token is None:
            self.cprint("Sensor is not registered yet. Wait for REGISTRATION_ACK")
            return False

        storage["is_data_ack"] = False
        storage["data_sent_at"] = time.time()

        transport.sendto(
            pkt.SensorDataPkt(token=token, payload=payload, is_low_battery=is_low_battery),
            storage["server_addr"],
            force_invalid_crc=force_invalid_crc
        )

        return True

    async def _command_send(self, args: list[str]) -> None:
        if (sensor := await self._select_sensor(args)) is None:
            return

        storage = sensor.storage
        low_battery_input = await asyncio.to_thread(input, "Low battery? (y/N): ")
        is_low_battery = low_battery_input.strip().lower() in {"y", "yes", "true", "1"}

        payload = {}
        for field_name, min_value, max_value, decimals in storage["configuration"]["fields"]:
            payload[field_name] = await self._prompt_field(field_name, min_value, max_value, decimals)

        if not self._send_packet(sensor, payload, is_low_battery):
            return

        self.cprint("Packet sent successfully")

    def _command_auto(self, args: list[str]) -> None:
        if len(args) < 1:
            self.cprint("Usage: auto <on/off>")
            return

        state = args[0].lower()
        if state not in {"on", "off"}:
            self.cprint("State must be either 'on' or 'off'")
            return

        for sensor in self._sensors:
            sensor.storage["auto_sending"] = state == "on"
            if state == "off":
                sensor.storage["data_sent_at"] = None
                sensor.storage["is_data_ack"] = True

        self.cprint(f"Automatic sending for all sensors is now {state}")

    async def _command_crc(self, args: list[str]) -> None:
        if (sensor := await self._select_sensor(args)) is None:
            return

        storage = sensor.storage
        payload = generate_sensor_payload(storage["configuration"]["fields"])
        if not self._send_packet(sensor, payload, False, force_invalid_crc=True):
            return

        self.cprint("The sent packet from this sensor have an invalid CRC")

    async def _command_check_alive(self, args: list[str]) -> None:
        if (sensor := await self._select_sensor(args)) is None:
            return

        sensor.storage["auto_sending"] = False
        sensor.storage["check_alive_test"] = {"attempts": 0}
        sensor.storage["data_sent_at"] = None
        sensor.storage["is_data_ack"] = True
        self.cprint(
            "CHECK_ALIVE test enabled. Automatic sending disabled until you re-enable it"
        )

    async def _prompt_field(
        self,
        field_name: str,
        min_value: float,
        max_value: float,
        decimals: int,
    ) -> int | float:
        while True:
            raw_value = await asyncio.to_thread(
                input,
                f"Enter value for {field_name} [{min_value}..{max_value}] (max {decimals} decimals): ",
            )

            try:
                decimal_value = Decimal(raw_value)
            except InvalidOperation:
                self.cprint("Invalid number. Please try again")
                continue

            if decimal_value < Decimal(str(min_value)) or decimal_value > Decimal(str(max_value)):
                self.cprint("Value out of allowed range. Try again")
                continue

            if decimals == 0 and decimal_value != decimal_value.to_integral_value():
                self.cprint("This field requires an integer value")
                continue

            if 0 < decimals < -decimal_value.as_tuple().exponent:
                self.cprint(f"Too many decimal places (allowed: {decimals})")
                continue

            if decimals == 0:
                return int(decimal_value)

            return float(decimal_value)

    async def _select_sensor(self, args: list[str]) -> SensorRuntime | None:
        if not args:
            sensors_text = " | ".join([
                f"({idx}) {sensor.identifier}" for idx, sensor in enumerate(self._sensors, start=1)
            ])
            if not sensors_text:
                self.cprint("No sensors available")
                return None

            cmd_input = await asyncio.to_thread(input, f"Select sensor [{sensors_text}]: ")
            if cmd_input is None:
                self.cprint("Sensor identifier is required")
                return None

            selector = cmd_input.strip().lower()
        else:
            cmd_input = args[0]
            selector = cmd_input.lower()

        for idx, sensor in enumerate(self._sensors, start=1):
            if selector == str(idx) or selector == sensor.identifier.lower():
                return sensor

        self.cprint(f"Sensor '{cmd_input}' was not found")
        return None

    def get_transports(self) -> list[DatagramTransport]:
        return self._transports
