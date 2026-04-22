from zoneinfo import available_timezones

_IANA_TIMEZONES = frozenset(available_timezones())


class Baby:
    def __init__(self, baby_id: int|None, name: str, timezone: str):
        self.id = baby_id
        self.name = name
        self.timezone = timezone #for now IANA timezone name on creation

    def validate_timezone(self) -> None:
        if self.timezone not in _IANA_TIMEZONES:
            raise ValueError(f"Invalid timezone: {self.timezone}. Use IANA style.")