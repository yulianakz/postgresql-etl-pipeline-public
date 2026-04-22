from datetime import datetime

class Sleep:
    def __init__(self, sleep_id: int|None, sleep_start: datetime, sleep_duration: int, baby_id: int):
        self.id = sleep_id
        self.start = sleep_start
        self.duration = sleep_duration
        self.baby_id = baby_id
