BITS_COUNT_TO_STRUCT = {
    8: "B",
    16: "H",
}
SENSOR_TYPE_TO_INT = {
    "TEMP": 0,
    "WIND": 1,
    "RAIN": 2,
    "AIR": 4
}
INT_TO_SENSOR_TYPE = {v: k for k, v in SENSOR_TYPE_TO_INT.items()}
