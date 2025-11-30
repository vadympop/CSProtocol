from typing import Any

SENSORS_CONFIGURATION = [
    {
        "default_port": 5001,
        "sensor_type": "TEMP",
        "fields": [
            ("temperature", -50, 60, 1), # field_name, min, max, zeros after comma
            ("humidity", 0, 100, 1),
            ("dew_point", -50, 60, 1),
            ("pressure", 800, 1100, 2),
        ]
    },
    {
        "default_port": 5002,
        "sensor_type": "WIND",
        "fields": [
            ("wind_speed", 0, 50, 1),
            ("wind_gust", 0, 70, 1),
            ("wind_direction", 0, 359, 0),
            ("turbulence", 0, 1, 1),
        ]
    },
    {
        "default_port": 5003,
        "sensor_type": "RAIN",
        "fields": [
            ("rainfall", 0, 500, 1),
            ("soil_moisture", 0, 100, 1),
            ("flood_risk", 0, 3, 0),
            ("rain_duration", 0, 60, 0),
        ]
    },
    {
        "default_port": 5004,
        "sensor_type": "AIR",
        "fields": [
            ("co2", 300, 5000, 1),
            ("ozone", 0, 500, 1),
            ("air_quality_index", 0, 500, 0)
        ]
    }
]

_TYPES_QUERY_MAPPING = ("t", "w", "r", "a")
_FIELDS_ATTRS_QUERY_MAPPING = ("name", "min", "max", "decimals")

def get_sensors_field_attr(query: str) -> Any:
    """
    Use to get value of attribute from sensors config, in this format: <sensor_type>.<field_name>.<field_attr>
    :param query: str
    :return: value of queried attribute
    """
    split_query = query.split(".")
    if len(split_query) != 3:
        raise ValueError("Invalid query format")

    try:
        type_index = _TYPES_QUERY_MAPPING.index(split_query[0])
        attr_index = _FIELDS_ATTRS_QUERY_MAPPING.index(split_query[2])
    except ValueError:
        raise ValueError("Invalid query params")

    sensor_config_fields = SENSORS_CONFIGURATION[type_index]["fields"]
    field_name = split_query[1]
    field_index = next((i for i, field in enumerate(sensor_config_fields) if field[0] == field_name), None)
    if field_index is None:
        raise ValueError("Invalid field name")

    return SENSORS_CONFIGURATION[type_index]["fields"][field_index][attr_index]


