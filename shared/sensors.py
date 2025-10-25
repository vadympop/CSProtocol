import time
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class SensorInfo:
    addr: Tuple[str, int]
    sensor_type: str
    last_seen: float
    token: int
    alive: bool = True


class SensorManager:
    def __init__(self, timeout: float = 15.0) -> None:
        self._sensors: Dict[Tuple[str, int], SensorInfo] = {}
        self.timeout = timeout

    def register(self, addr: Tuple[str, int], sensor_type: str, token: int) -> None:
        if addr not in self._sensors:
            print(f"[+] Registered sensor {sensor_type} @ {addr}")

        self._sensors[addr] = SensorInfo(addr, sensor_type, time.time(), token, True)

    def update(self, addr: Tuple[str, int]) -> None:
        if addr in self._sensors:
            self._sensors[addr].last_seen = time.time()
            if not self._sensors[addr].alive:
                self._sensors[addr].alive = True
                print(f"[✓] Sensor {addr} reconnected")
        else:
            print(f"[?] Unregistered sensor sent data from {addr}")

    def mark_inactive(self) -> None:
        now = time.time()
        for s in self._sensors.values():
            if s.alive and now - s.last_seen > self.timeout:
                s.alive = False
                print(f"[x] Sensor {s.addr} timed out (inactive)")

    def all_sensors(self) -> list[SensorInfo]:
        return list(self._sensors.values())

    def alive_sensors(self) -> list[SensorInfo]:
        return [s for s in self._sensors.values() if s.alive]
