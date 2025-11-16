from typing import Dict

from .fields import ScalarPayloadField, CombinedPayloadField
from .serializer import PayloadSerializer


class TemperaturePayloadSerializer(PayloadSerializer):
    type_name = "TEMP"
    code = 0
    field_definitions = (
        ScalarPayloadField("temperature", "h"),
        ScalarPayloadField("humidity", "H"),
        ScalarPayloadField("dew_point", "h"),
        ScalarPayloadField("pressure", "H"),
    )


class WindPayloadSerializer(PayloadSerializer):
    type_name = "WIND"
    code = 1
    field_definitions = (
        ScalarPayloadField("wind_speed", "H"),
        ScalarPayloadField("wind_gust", "H"),
        ScalarPayloadField("wind_direction", "H"),
        ScalarPayloadField("turbulence", "B"),
    )


class RainPayloadSerializer(PayloadSerializer):
    type_name = "RAIN"
    code = 2
    field_definitions = (
        ScalarPayloadField("rainfall", "H"),
        ScalarPayloadField("soil_moisture", "H"),
        CombinedPayloadField(("flood_risk", "rain_duration"), (2, 6)),
    )


class AirPayloadSerializer(PayloadSerializer):
    type_name = "AIR"
    code = 3
    field_definitions = (
        ScalarPayloadField("co2", "H"),
        ScalarPayloadField("ozone", "H"),
        ScalarPayloadField("air_quality_index", "H"),
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