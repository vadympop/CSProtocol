import asyncio
from typing import Callable

from shared.cli.base import BaseCLI
from shared.sensors.manager import SensorInfo


HELP_MSG = (
    "Available commands:\n"
    "  help / ?     - Show this help message\n"
    "  status       - Display server socket information\n"
    "  sensors      - List registered sensors\n"
    "  skip_ack     - Skip the next DATA_ACK response\n"
    "  exit / quit  - Stop the server"
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

        cmd = parts[0].lower()

        if cmd in {"help", "?"}:
            self._print_help()
        elif cmd == "status":
            self._print_status()
        elif cmd == "skip_ack":
            self._storage["skip_data_ack_remaining"] = 3
            self.cprint("The next 3 DATA_ACK packets will be skipped")
        elif cmd == "sensors":
            self._print_sensors()
        elif cmd in {"quit", "exit"}:
            await self._shutdown()
        else:
            self.cprint(f"Unknown command: {cmd}. Type 'help' for a list of commands")

    def _print_status(self) -> None:
        address = self._get_address()
        pending_skip_count = self._storage.get("skip_data_ack_remaining", 0)
        self.cprint(
            f"Server bound to {address[0]}:{address[1]}\n"
            f"Skip next DATA_ACK count: {pending_skip_count if pending_skip_count else 'disabled'}"
        )

    def _print_sensors(self) -> None:
        sensors = self._get_sensors()
        if not sensors:
            self.cprint("No sensors registered yet")
            return

        for sensor in sensors:
            status = "alive" if sensor.alive else "disconnected"
            self.cprint(
                f"- {sensor.sensor_type} @ {sensor.addr[0]}:{sensor.addr[1]}"
                f" | token={sensor.token} | status={status}"
            )
