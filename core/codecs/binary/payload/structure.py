from typing import Dict

from core.configs.sensors_config import get_sensors_field_attr
from .fields import BoundedPayloadField, ShiftedDynamicPayloadField
from .serializer import PayloadSerializer


class TemperaturePayloadSerializer(PayloadSerializer):
    type_name = "TEMP"
    code = 0
    field_definitions = (
        BoundedPayloadField("temperature", 1, get_sensors_field_attr("t.temperature.max")),
        BoundedPayloadField("humidity", 1, get_sensors_field_attr("t.humidity.max")),
        BoundedPayloadField("dew_point", 1, get_sensors_field_attr("t.dew_point.max")),
        ShiftedDynamicPayloadField(
            "pressure",
            get_sensors_field_attr("t.pressure.decimals"),
            get_sensors_field_attr("t.pressure.min"),
            get_sensors_field_attr("t.pressure.max")
        ),
    )


class WindPayloadSerializer(PayloadSerializer):
    type_name = "WIND"
    code = 1
    field_definitions = (
        BoundedPayloadField("wind_speed", 1, get_sensors_field_attr("w.wind_speed.max")),
        BoundedPayloadField("wind_gust", 1, get_sensors_field_attr("w.wind_gust.max")),
        BoundedPayloadField("wind_direction", 0, get_sensors_field_attr("w.wind_direction.max")),
        BoundedPayloadField("turbulence", 1, get_sensors_field_attr("w.turbulence.max")),
    )


class RainPayloadSerializer(PayloadSerializer):
    type_name = "RAIN"
    code = 2
    field_definitions = (
        BoundedPayloadField("rainfall", 1, get_sensors_field_attr("r.rainfall.max")),
        BoundedPayloadField("soil_moisture", 1, get_sensors_field_attr("r.soil_moisture.max")),
        BoundedPayloadField("flood_risk", 0, get_sensors_field_attr("r.flood_risk.max")),
        BoundedPayloadField("rain_duration", 0, get_sensors_field_attr("r.rain_duration.max")),
    )


class AirPayloadSerializer(PayloadSerializer):
    type_name = "AIR"
    code = 3
    field_definitions = (
        ShiftedDynamicPayloadField(
            "co2",
            get_sensors_field_attr("a.co2.decimals"),
            get_sensors_field_attr("a.co2.min"),
            get_sensors_field_attr("a.co2.max")
        ),
        BoundedPayloadField("ozone", 1, get_sensors_field_attr("a.ozone.max")),
        BoundedPayloadField("air_quality_index", 0, get_sensors_field_attr("a.air_quality_index.max")),
    )


def _build_registry() -> tuple[PayloadSerializer, ...]:
    serializers: tuple[type[PayloadSerializer], ...] = (
        TemperaturePayloadSerializer,
        WindPayloadSerializer,
        RainPayloadSerializer,
        AirPayloadSerializer,
    )
    instances = tuple(serializer() for serializer in serializers)
    return instances


_PAYLOAD_SERIALIZERS: tuple[PayloadSerializer, ...] = _build_registry()
_SERIALIZERS_BY_NAME: Dict[str, PayloadSerializer] = {
    serializer.type_name: serializer for serializer in _PAYLOAD_SERIALIZERS
}
_SERIALIZERS_BY_CODE: Dict[int, PayloadSerializer] = {
    serializer.code: serializer for serializer in _PAYLOAD_SERIALIZERS
}


def get_serializer_by_code(code: int) -> PayloadSerializer:
    try:
        return _SERIALIZERS_BY_CODE[code]
    except KeyError as e:
        raise ValueError(f"Unknown sensor type code: {code}") from e


def get_serializer_by_name(name: str) -> PayloadSerializer:
    try:
        return _SERIALIZERS_BY_NAME[name]
    except KeyError as e:
        raise ValueError(f"Unknown sensor type '{name}'") from e