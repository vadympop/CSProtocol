import asyncio

from abc import ABC, abstractmethod
from typing import Callable


class BaseCLI(ABC):
    def __init__(
        self,
        welcome_msg: str,
        help_msg: str,
        shutdown_callback: Callable[[], None] | Callable[[], asyncio.Future],
    ) -> None:
        self.welcome_msg = welcome_msg
        self.help_msg = help_msg

        self._shutdown_callback = shutdown_callback
        self._running = True

    async def run(self) -> None:
        self.cprint(self.welcome_msg)
        self._print_help()

        while self._running:
            try:
                raw_command = await asyncio.to_thread(input, "command> ")
            except (EOFError, KeyboardInterrupt):
                await self._shutdown()
                break

            command = raw_command.strip()
            if not command:
                continue

            await self._handle_command(command)

    @abstractmethod
    async def _handle_command(self, command: str) -> None:
        raise NotImplementedError()

    def cprint(self, text: str) -> None:
        print("\n", text, "\n")

    def _print_help(self) -> None:
        self.cprint(self.help_msg)

    async def _shutdown(self) -> None:
        if not self._running:
            return

        self._running = False
        result = self._shutdown_callback()
        if asyncio.iscoroutine(result):
            await result