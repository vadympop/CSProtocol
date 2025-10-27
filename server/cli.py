import asyncio
import shlex
from typing import Callable

from shared.logger import Logger
from shared.sensors.manager import SensorInfo


class ServerCLI:
    def __init__(
        self,
        *,
        storage: dict,
        get_sensors: Callable[[], list[SensorInfo]],
        get_address: Callable[[], tuple[str, int]],
        shutdown_callback: Callable[[], None] | Callable[[], asyncio.Future],
    ) -> None:
        self._storage = storage
        self._get_sensors = get_sensors
        self._get_address = get_address
        self._shutdown_callback = shutdown_callback
        self._running = True

    async def run(self) -> None:
        print("Server CLI started. Type 'help' to list commands.")

        while self._running:
            try:
                raw_command = await asyncio.to_thread(input, "server> ")
            except (EOFError, KeyboardInterrupt):
                await self._shutdown()
                break

            command = raw_command.strip()
            if not command:
                continue

            await self._handle_command(command)

    async def _handle_command(self, command: str) -> None:
        parts = shlex.split(command)
        if not parts:
            return

        cmd = parts[0].lower()

        if cmd in {"help", "?"}:
            self._print_help()
        elif cmd == "status":
            self._print_status()
        elif cmd == "skip_ack":
            self._storage["skip_next_ack"] = True
            print("The next DATA_ACK packet will be skipped.")
        elif cmd == "sensors":
            self._print_sensors()
        elif cmd in {"quit", "exit"}:
            await self._shutdown()
        else:
            print(f"Unknown command: {cmd}. Type 'help' for a list of commands.")

    def _print_help(self) -> None:
        print(
            "Available commands:\n"
            "  help / ?     - Show this help message\n"
            "  status       - Display server socket information\n"
            "  sensors      - List registered sensors\n"
            "  skip_ack     - Skip the next DATA_ACK response\n"
            "  exit / quit  - Stop the server"
        )

    def _print_status(self) -> None:
        address = self._get_address()
        pending_skip = self._storage.get("skip_next_ack", False)
        print(
            f"Server bound to {address[0]}:{address[1]}\n"
            f"Skip next DATA_ACK: {'enabled' if pending_skip else 'disabled'}"
        )

    def _print_sensors(self) -> None:
        sensors = self._get_sensors()
        if not sensors:
            print("No sensors registered yet.")
            return

        for sensor in sensors:
            status = "alive" if sensor.alive else "disconnected"
            Logger.log_debug(
                f"Sensor {sensor.sensor_type} status requested via CLI: {status}"
            )
            print(
                f"- {sensor.sensor_type} @ {sensor.addr[0]}:{sensor.addr[1]}"
                f" | token={sensor.token} | status={status}"
            )

    async def _shutdown(self) -> None:
        if not self._running:
            return

        self._running = False
        result = self._shutdown_callback()
        if asyncio.iscoroutine(result):
            await result