import asyncio
from typing import Callable

from shared.cli.base import BaseCLI
from shared.sensors.manager import SensorInfo


HELP_MSG = (
    "Available commands:\n"
    "  help / ?          - Show this help message\n"
    "  status            - Display server socket information\n"
    "  sensors           - List registered sensors\n"
    "  skip_ack <sensor> - Skip the next DATA_ACK response\n"
    "  exit / quit       - Stop the server"
)
WELCOME_MSG = "Server CLI started. Type 'help' to list commands."


class ServerCLI(BaseCLI):
    def __init__(
            self,
            *,
            storage: dict,
            get_sensors: Callable[[], list[SensorInfo]],
            get_address: Callable[[], tuple[str, int]],
            shutdown_callback: Callable[[], None] | Callable[[], asyncio.Future],
    ) -> None:
        super().__init__(
            help_msg=HELP_MSG,
            welcome_msg=WELCOME_MSG,
            shutdown_callback=shutdown_callback
        )

        self._storage = storage
        self._get_sensors = get_sensors
        self._get_address = get_address

    async def _handle_command(self, command: str) -> None:
        parts = command.split(" ")
        if not parts:
            return

        cmd, *args = parts
        cmd = cmd.lower()

        if cmd in {"help", "?"}:
            self._print_help()
        elif cmd == "status":
            self._print_status()
        elif cmd == "skip_ack":
            self._command_skip_ack(args)
        elif cmd == "sensors":
            self._print_sensors()
        elif cmd in {"quit", "exit"}:
            await self._shutdown()
        else:
            self.cprint(f"Unknown command: {cmd}. Type 'help' for a list of commands")

    def _command_skip_ack(self, args: list[str]) -> None:
        if (sensor := self._resolve_sensor(args)) is None:
            return

        self._storage["skip_data_ack_remaining"][sensor.addr] = 3
        self.cprint(f"The next 3 DATA_ACK packets for {sensor.sensor_type} sensor will be skipped")

    def _print_status(self) -> None:
        address = self._get_address()
        pending_skip = self._storage.get("skip_data_ack_remaining", {})
        sensors_types = {x.addr: x.sensor_type for x in self._get_sensors()}

        if not pending_skip:
            skip_ack_text = "disabled"
        else:
            skip_ack_text = ", ".join([f"{sensors_types[k]} - {v}" for k, v in pending_skip.items()])

        self.cprint(
            f"Server bound to {address[0]}:{address[1]}\n"
            f"Skip next DATA_ACK count: {skip_ack_text}"
        )

    def _print_sensors(self) -> None:
        sensors = self._get_sensors()
        if not sensors:
            self.cprint("No sensors registered yet")
            return

        for idx, sensor in enumerate(sensors):
            status = "alive" if sensor.alive else "disconnected"
            self.cprint(
                f"- [{idx}] {sensor.sensor_type} @ {sensor.addr[0]}:{sensor.addr[1]}"
                f" | token={sensor.token} | status={status}"
            )

    def _resolve_sensor(self, args: list[str]) -> SensorInfo | None:
        if not args:
            self.cprint("Sensor type is required")
            return None

        selector = args[0].lower()

        for idx, sensor in enumerate(self._get_sensors(), start=1):
            if selector == str(idx) or selector == sensor.sensor_type.lower():
                return sensor

        self.cprint(f"Sensor '{args[0]}' was not found")
        return None
