import random


def generate_sensor_value(min_value: float, max_value: float, decimal: int) -> int | float:
    result = round(random.uniform(min_value, max_value), decimal)
    if decimal == 0:
        return int(result)

    return result

def generate_sensor_payload(fields: list[tuple]) -> dict[str, int | float]:
    return {
        x[0]: generate_sensor_value(*x[1:]) for x in fields
    }
