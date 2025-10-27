import asyncio
import time
from typing import TYPE_CHECKING

from shared.logger import Logger
from shared.tasks import BackgroundTask, BackgroundTasksManager

if TYPE_CHECKING:
    from .manager import SensorManager, SensorInfo


class SensorsTasksManager:
    def __init__(self, manager: "SensorManager", background_tasks: BackgroundTasksManager):
        self.manager: "SensorManager" = manager
        self.background_tasks: BackgroundTasksManager = background_tasks

    def mark_inactive_task(self) -> None:
        now = time.time()
        for s in self.manager.all_sensors():
            if s.alive and now - s.last_seen > 15:
                s.alive = False

                self.manager.send_check_alive(s, True)
                # Send first check alive packet and wait for response 1sec
                # If response doesnt come start tasks:
                # 1. Every 10sec print DISCONNECTED msg
                # 2. Every 5sec send check alive packet max 10 attempts
                Logger.log_debug(f"Sensor {s.sensor_type} timed out(first 15sec)")

    def mark_disconnected_task(self) -> None:
        now = time.time()
        for s in self.manager.all_sensors():
            if not s.alive and not s.disconnected and now - s.first_check_alive_time > 1:
                s.disconnected = True
                self.start_disconnected_tasks(s)

    async def repeated_check_alive_task(self, sensor: "SensorInfo") -> None:
        attempts = 0
        while attempts < 10:
            self.manager.send_check_alive(sensor)
            attempts += 1

            await asyncio.sleep(5)

        # Unregister sensor if sensor doesnt reply and task wasnt cancelled earlier
        self.manager.unregister(sensor.addr)

    def start_base_tasks(self) -> None:
        self.background_tasks.add_task(
            "sensors_mark_inactive", BackgroundTask(self.mark_inactive_task, 1)
        )
        self.background_tasks.add_task(
            "sensors_mark_disconnected", BackgroundTask(self.mark_disconnected_task, 1)
        )

    def start_disconnected_tasks(self, sensor: "SensorInfo") -> None:
        sensor_id = sensor.sensor_type
        self.background_tasks.add_task(
            f"sensor_{sensor_id}_disconnected",
            BackgroundTask(lambda: Logger.disconnected(sensor_id), 10)
        )
        self.background_tasks.add_task(
            f"sensor_{sensor_id}_check_alive",
            self.repeated_check_alive_task,
            sensor=sensor
        )

    def cancel_sensor_tasks(self, sensor: "SensorInfo") -> None:
        sensor_id = sensor.sensor_type

        self.background_tasks.cancel(
            f"sensor_{sensor_id}_disconnected", f"sensor_{sensor_id}_check_alive"
        )
