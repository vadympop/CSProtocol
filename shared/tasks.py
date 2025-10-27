import asyncio
from asyncio import Task
from typing import Callable


class BackgroundTask:
    def __init__(self, func: Callable, timeout: float) -> None:
        self._func = func
        self.timeout = timeout

    async def _wrapped_task(self, **kwargs) -> None:
        while True:
            self._func(**kwargs)
            await asyncio.sleep(self.timeout)

    def start(self, **kwargs) -> Task:
        return asyncio.create_task(self._wrapped_task(**kwargs))


class TasksManager:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add_task(self, task_id: str, func: BackgroundTask | Callable, **kwargs) -> None:
        if isinstance(func, BackgroundTask):
            self._tasks[task_id] = func.start(**kwargs)
            return

        self._tasks[task_id] = asyncio.create_task(func(**kwargs))

    def cancel_all(self) -> None:
        for task in self._tasks.values():
            task.cancel()

        self._tasks = {}

    def cancel(self, *tasks_id: str) -> None:
        for x in tasks_id:
            if x not in self._tasks:
                continue

            task = self._tasks.pop(x)
            task.cancel()
