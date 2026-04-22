from datetime import datetime

class Diaper:

    VALID_STATUSES = {"wet", "dirty", "mixed"}

    def __init__(self, diaper_id: int|None, change_time: datetime, status: str, baby_id: int):
        self.id = diaper_id
        self.change_time = change_time
        self.status = status.strip().lower()
        self.baby_id = baby_id

    def validate_status(self) -> None:
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid diaper status: {self.status}")
