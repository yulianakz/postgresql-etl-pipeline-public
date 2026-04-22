from etl.extract.domain.mappers.exceptions import MapperError
from datetime import datetime

def _normalize(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    return value


def safe_int(value):
    value = _normalize(value)
    if value is None:
        return None
    try:
        parsed = int(value)
        if parsed < 0:
            raise MapperError(
                value=value,
                expected_type="non-negative int",
                original_error=ValueError("Negative integers are not allowed"),
            )
    except (ValueError, TypeError) as e:
        raise MapperError(value=value, expected_type="int", original_error=e)
    return parsed


def safe_datetime(value, fmt=None):
    if isinstance(value, datetime):
        return value

    value = _normalize(value)
    if value is None:
        return None

    common_formats = [
        "%Y-%m-%dT%H:%M:%S%z",  # ISO with timezone: "2024-01-28T19:08:00+00:00"
        "%Y-%m-%dT%H:%M%z",     # ISO with timezone no seconds: "2024-01-28T19:08+00:00"
        "%Y-%m-%d %H:%M",     # ISO-like: "2024-02-02 08:00"
        "%Y-%m-%d %H:%M:%S",  # ISO with seconds: "2024-02-02 08:00:00"
        "%Y-%m-%dT%H:%M",     # ISO format: "2024-02-02T08:00"
        "%Y-%m-%dT%H:%M:%S",  # ISO with seconds: "2024-02-02T08:00:00"
        "%d.%m.%Y, %H:%M",    # European: "02.02.2024, 08:00"
        "%d.%m.%Y %H:%M",     # European without comma: "02.02.2024 08:00"
        "%d/%m/%Y %H:%M",     # US format: "02/02/2024 08:00"
        "%m/%d/%Y %H:%M",     # US format: "02/02/2024 08:00"
    ]

    try:
        formats_to_try: list[str] = []
        last_error: Exception | None = None

        if fmt:
            formats_to_try.append(fmt)

        formats_to_try.extend(f for f in common_formats if f != fmt)

        for fmt_to_try in formats_to_try:
            try:
                return datetime.strptime(value, fmt_to_try)
            except (ValueError, TypeError) as e:
                last_error = e
                continue

        if last_error is not None:
            raise last_error
        else:
            raise ValueError(f"Could not parse {value!r} as datetime")

    except (ValueError, TypeError) as e:
        raise MapperError(value=value, expected_type="datetime", original_error=e)


def safe_str(value):
    return _normalize(value)