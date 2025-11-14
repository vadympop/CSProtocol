from asyncio import DatagramTransport
from typing import Callable, Awaitable

from client.consts import DEFAULT_SERVER_ADDR
from shared.cli.base import BaseCLI, ShutdownCallbackType
from shared.cli.utils import prompt_ip, prompt_port
from shared.types import RemoteAddr
from shared.sensors.manager import SensorInfo


HELP_MSG = (
    "Available commands:\n"
    "  help / ?          - Show this help message\n"
    "  status            - Display server socket information\n"
    "  sensors           - List registered sensors\n"
    "  skip_ack <sensor> - Skip the next DATA_ACK response\n"
    "  configure         - Configure and start the server\n"
    "  exit / quit       - Stop the server"
)
WELCOME_MSG = "Server CLI started. Type 'configure' to start the server or 'help' to list commands."


class ServerCLI(BaseCLI):
    def __init__(
            self,
            start_hook: Callable[["ServerCLI", RemoteAddr], Awaitable[DatagramTransport]],
            shutdown_callback: ShutdownCallbackType,
    ) -> None:
        super().__init__(
            help_msg=HELP_MSG,
            welcome_msg=WELCOME_MSG,
            shutdown_callback=shutdown_callback
        )

        self._transport = None
        self.is_configured = False
        self.start_hook = start_hook
        self._storage = None
        self._get_sensors = None
        self._get_address = None

    def init(
            self,
            *,
            storage: dict,
            transport: DatagramTransport,
            get_sensors: Callable[[], list[SensorInfo]],
            get_address: Callable[[], tuple[str, int]],
    ) -> None:
        self.is_configured = True
        self._storage = storage
        self._get_sensors = get_sensors
        self._get_address = get_address
        self._transport = transport

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
        elif cmd == "configure":
            await self._command_configure()
        elif cmd in {"quit", "exit"}:
            await self._shutdown()
        else:
            self.cprint(f"Unknown command: {cmd}. Type 'help' for a list of commands")

    def _command_skip_ack(self, args: list[str]) -> None:
        if not self._assert_running():
            return

        if (sensor := self._resolve_sensor(args)) is None:
            return

        self._storage["skip_data_ack_remaining"][sensor.addr] = 3
        self.cprint(f"The next 3 DATA_ACK packets for {sensor.sensor_type} sensor will be skipped")

    async def _command_configure(self) -> None:
        if self.is_configured:
            self.cprint("Server already configured")
            return

        server_ip = prompt_ip("Enter server IP", DEFAULT_SERVER_ADDR[0])
        server_port = prompt_port("Enter server port", DEFAULT_SERVER_ADDR[1])

        await self.start_hook(self, (server_ip, server_port))
        self.cprint("Server configured and running")

    def _print_status(self) -> None:
        if not self._assert_running():
            return

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
        if not self._assert_running():
            return

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

    def _assert_running(self) -> bool:
        if self.is_configured:
            return True

        self.cprint("Server is not running. Use 'configure' to start it.")
        return False

    def get_transport(self) -> DatagramTransport:
        return self._transport
