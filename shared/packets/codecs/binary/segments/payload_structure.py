PAYLOAD_STRUCTURE = { # H - uint16(2 bytes), h - int16, B - uint8(1 byte)
    "TEMP": [
        ("temperature", "h"),
        ("humidity", "H"),
        ("dew_point", "h"),
        ("pressure", "H"),
    ],
    "WIND": [
        ("wind_speed", "H"),
        ("wind_gust", "H"),
        ("wind_direction", "H"),
        ("turbulence", "B"),
    ],
    "RAIN": [
        ("rainfall", "H"),
        ("soil_moisture", "H"),
        (["flood_risk", "rain_duration"], [2, 6]), # 2 and 6 bits
    ],
    "AIR": [
        ("co2", "H"),
        ("ozone", "H"),
        ("air_quality_index", "H"),
    ]
}
