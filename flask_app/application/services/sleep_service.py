from datetime import datetime, timezone

from flask_app.db.repository_interfaces.baby_repo_interface import BabyRepository
from flask_app.db.repository_interfaces.sleep_repo_interface import SleepRepository
from flask_app.domain.entities.sleep import Sleep


def _validate_positive_sleep_duration(sleep_duration: int) -> None:
    if sleep_duration <= 0:
        raise ValueError("Sleep duration must be positive")


def _sleep_start_utc(sleep_start: datetime) -> datetime:
    """Naive values are treated as UTC; aware values are converted to UTC."""
    if sleep_start.tzinfo is None:
        return sleep_start.replace(tzinfo=timezone.utc)
    return sleep_start.astimezone(timezone.utc)


class SleepService:

    def __init__(self, sleep_repo: SleepRepository, baby_repo: BabyRepository):
        self.sleep_repo = sleep_repo
        self.baby_repo = baby_repo

    def create_sleep(self, sleep_start: datetime, sleep_duration: int, baby_id: int) -> Sleep:
        _validate_positive_sleep_duration(sleep_duration)
        sleep_start = _sleep_start_utc(sleep_start)
        if sleep_start > datetime.now(timezone.utc):
            raise ValueError("Sleep start cannot be in the future")
        if baby_id <=0:
            raise ValueError("Invalid baby id")

        baby = self.baby_repo.get_by_id(baby_id)
        if baby is None:
            raise ValueError("Baby id does not exist")

        sleep = Sleep(sleep_id=None,sleep_start=sleep_start, sleep_duration=sleep_duration, baby_id=baby_id)
        return self.sleep_repo.create_sleep(sleep)

    def get_sleep_by_baby_id(self, baby_id: int) -> list[Sleep]:
        if baby_id <=0:
            raise ValueError("Invalid baby id")

        baby = self.baby_repo.get_by_id(baby_id)
        if baby is None:
            raise ValueError("Baby id does not exist")

        return self.sleep_repo.get_by_baby_id(baby_id)

    def get_sleep_by_sleep_id(self, baby_id:int, sleep_id: int) -> Sleep|None:
        if sleep_id <=0:
            raise ValueError("Invalid sleep id")
        if baby_id <=0:
            raise ValueError("Invalid baby id")

        sleep = self.sleep_repo.get_by_sleep_id(sleep_id)
        if sleep is None:
            return None

        if sleep.baby_id != baby_id:
            raise PermissionError("Sleep does not belong to this baby")
        return sleep

    def update_sleep(self,baby_id:int, sleep_id: int, sleep_start: datetime, sleep_duration: int) -> Sleep|None:
        _validate_positive_sleep_duration(sleep_duration)
        sleep_start = _sleep_start_utc(sleep_start)
        if sleep_start > datetime.now(timezone.utc):
            raise ValueError("Sleep start cannot be in the future")

        sleep = self.get_sleep_by_sleep_id(baby_id, sleep_id)
        if sleep is None:
            return None

        sleep.start = sleep_start
        sleep.duration = sleep_duration
        return self.sleep_repo.update_sleep(sleep)

    def delete_sleep_by_id(self, baby_id, sleep_id: int) -> Sleep|None:
        if baby_id <= 0 or sleep_id <= 0:
            raise ValueError("Invalid id")

        sleep = self.get_sleep_by_sleep_id(baby_id, sleep_id)
        if sleep is None:
            return None

        return self.sleep_repo.delete_sleep(sleep_id)
