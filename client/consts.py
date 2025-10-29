HANDLERS_INITIAL_STORAGE = {
    "is_data_ack": False,
    "data_sent_at": None,
    "register_sent_at": None,
    "is_register_ack": False,
    "token": None,
    "auto_sending": False,
    "check_alive_test": None
}
DEFAULT_SERVER_ADDR = ("127.0.0.1", 5000)
DEFAULT_SENSOR_IP = "127.0.0.1"
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
        "port": 5002,
        "sensor_type": "WIND",
        "fields": [
            ("wind_speed", 0, 50, 1),
            ("wind_gust", 0, 70, 1),
            ("wind_direction", 0, 359, 0),
            ("turbulence", 0, 1, 1),
        ]
    },
    {
        "port": 5003,
        "sensor_type": "RAIN",
        "fields": [
            ("rainfall", 0, 500, 1),
            ("soil_moisture", 0, 100, 1),
            ("flood_risk", 0, 3, 0),
            ("rain_duration", 0, 60, 0),
        ]
    },
    {
        "port": 5004,
        "sensor_type": "AIR",
        "fields": [
            ("co2", 300, 5000, 1),
            ("ozone", 0, 500, 1),
            ("air_quality_index", 0, 500, 0)
        ]
    }
]
