import datetime
from typing import Any


class Logger:
    debug: bool = False

    @classmethod
    def set_config(cls, debug: bool) -> None:
        cls.debug = debug

    @classmethod
    def log_debug(cls, msg: str) -> None:
        if not cls.debug:
            return

        print(f"DEBUG - {datetime.datetime.now()}: {msg}")

    @classmethod
    def register(cls, sensor_id: str, timestamp: datetime.datetime) -> None:
        print(f"INFO: {sensor_id} REGISTERED at {timestamp}")

    @classmethod
    def data_received(
            cls,
            sensor_id: str,
            timestamp: datetime.datetime,
            is_low_battery: bool,
            payload: dict[str, Any]
    ) -> None:
        warning_msg = "WARNING: LOW BATTERY " if is_low_battery else ""
        payload_msg = "; ".join([f"{k}: {v}" for k, v in payload.items()])

        print(f"{timestamp} - {warning_msg}{sensor_id}\n")
        print(payload_msg)

    @classmethod
    def disconnected(cls, sensor_id: str) -> None:
        print(f"WARNING: {sensor_id} DISCONNECTED!")

    @classmethod
    def reconnected(cls, sensor_id: str) -> None:
        print(f"INFO: {sensor_id} RECONNECTED!")

    @classmethod
    def invalid_data(cls, sensor_id: str) -> None:
        print(f"INFO: {sensor_id} CORRUTPED DATA at {datetime.datetime.now()}. REQUESTING DATA")

