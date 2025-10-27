import asyncio
import shlex
import time

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Iterable

from shared import packet as pkt
from shared.cli.base import BaseCLI


HELP_MSG = (
    "Available commands:\n"
    "  help / ?                - Show this help message\n"
    "  status / list           - Show sensors status\n"
    "  send <sensor>           - Manually send a packet from sensor\n"
    "  auto <sensor> <on/off>  - Enable or disable automatic sending\n"
    "  crc <sensor>            - Corrupt the next packet's CRC\n"
    "  check_alive_test <sensor> - Enable the CHECK_ALIVE test mode\n"
    "  exit / quit             - Stop the client"
)
WELCOME_MSG = "Client CLI started. Type 'help' to list commands."


@dataclass
class SensorRuntime:
    identifier: str
    local_ip: str
    local_port: int
    storage: dict


class ClientCLI(BaseCLI):
    def __init__(
        self,
        sensors: Iterable[SensorRuntime],
        shutdown_callback: Callable[[], None] | Callable[[], asyncio.Future],
    ) -> None:
        self._sensors = list(sensors)

        super().__init__(
            welcome_msg=WELCOME_MSG,
            help_msg=HELP_MSG,
            shutdown_callback=shutdown_callback
        )

    async def _handle_command(self, command: str) -> None:
        parts = shlex.split(command)
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
            self._command_crc(args)
        elif cmd == "check_alive_test":
            self._command_check_alive(args)
        elif cmd in {"exit", "quit"}:
            await self._shutdown()
        else:
            self.cprint(f"Unknown command: {cmd}. Type 'help' for a list of commands")

    def _print_status(self) -> None:
        if not self._sensors:
            self.cprint("No sensors configured")
            return

        for idx, sensor in enumerate(self._sensors, start=1):
            storage = sensor.storage
            token = storage.get("token")
            auto_enabled = storage.get("auto_sending", True)
            waiting_ack = storage.get("data_sent_at") is not None and not storage.get("is_data_ack", True)
            crc_pending = storage.get("break_crc_once", False)
            check_alive_test = storage.get("check_alive_test")

            self.cprint(
                f"[{idx}] {sensor.identifier}"
                f" | local={sensor.local_ip}:{sensor.local_port}"
                f" | token={'-' if token is None else token}"
                f" | auto={'on' if auto_enabled else 'off'}"
                f" | waiting_ack={'yes' if waiting_ack else 'no'}"
                f" | crc_break={'yes' if crc_pending else 'no'}"
                f" | check_alive_test={'active' if check_alive_test else 'inactive'}"
            )

    async def _command_send(self, args: list[str]) -> None:
        sensor = self._resolve_sensor(args)
        if sensor is None:
            return

        storage = sensor.storage
        transport = storage.get("transport")
        if transport is None:
            self.cprint("Transport is not ready yet. Please wait for initialization")
            return

        token = storage.get("token")
        if token is None:
            self.cprint("Sensor is not registered yet. Wait for REGISTRATION_ACK")
            return

        payload = {}
        for field_name, min_value, max_value, decimals in storage["configuration"]["fields"]:
            payload[field_name] = await self._prompt_field(field_name, min_value, max_value, decimals)

        low_battery_input = await asyncio.to_thread(input, "Low battery? (y/N): ")
        is_low_battery = low_battery_input.strip().lower() in {"y", "yes", "true", "1"}

        storage["is_data_ack"] = False
        storage["data_sent_at"] = time.time()

        transport.sendto(
            pkt.SensorDataPkt(token=token, payload=payload, is_low_battery=is_low_battery),
            storage["server_addr"],
        )

        self.cprint("Packet sent successfully")

    def _command_auto(self, args: list[str]) -> None:
        if len(args) < 2:
            self.cprint("Usage: auto <sensor> <on/off>")
            return

        sensor = self._resolve_sensor([args[0]])
        if sensor is None:
            return

        state = args[1].lower()
        if state not in {"on", "off"}:
            self.cprint("State must be either 'on' or 'off'")
            return

        sensor.storage["auto_sending"] = state == "on"
        if state == "off":
            sensor.storage["data_sent_at"] = None
            sensor.storage["is_data_ack"] = True

        self.cprint(f"Automatic sending for {sensor.identifier} is now {state}")

    def _command_crc(self, args: list[str]) -> None:
        sensor = self._resolve_sensor(args)
        if sensor is None:
            return

        sensor.storage["break_crc_once"] = True
        self.cprint("The next packet from this sensor will have an invalid CRC")

    def _command_check_alive(self, args: list[str]) -> None:
        sensor = self._resolve_sensor(args)
        if sensor is None:
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

    def _resolve_sensor(self, args: list[str]) -> SensorRuntime | None:
        if not args:
            self.cprint("Sensor identifier is required")
            return None

        selector = args[0].lower()

        for idx, sensor in enumerate(self._sensors, start=1):
            if selector == str(idx) or selector == sensor.identifier.lower():
                return sensor

        self.cprint(f"Sensor '{args[0]}' was not found")
        return None

    @staticmethod
    def _consume_crc_flag(storage: dict) -> bool:
        if storage.get("break_crc_once"):
            storage["break_crc_once"] = False
            return True
        return False
