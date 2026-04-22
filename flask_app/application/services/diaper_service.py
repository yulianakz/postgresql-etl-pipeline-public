from datetime import datetime, timezone

from flask_app.db.repository_interfaces.baby_repo_interface import BabyRepository
from flask_app.db.repository_interfaces.diaper_repo_interface import DiaperRepository
from flask_app.domain.entities.diaper import Diaper

class DiaperService:

    def __init__(self, diaper_repo: DiaperRepository, baby_repo: BabyRepository):
        self.diaper_repo = diaper_repo
        self.baby_repo = baby_repo

    def create_diaper(self, change_time: datetime, status: str, baby_id: int) -> Diaper:
        if change_time > datetime.now(timezone.utc):
            raise ValueError("Sleep start cannot be in the future")
        if baby_id <=0:
            raise ValueError("Invalid baby id")

        baby = self.baby_repo.get_by_id(baby_id)
        if baby is None:
            raise ValueError("Baby id does not exist")

        diaper = Diaper(diaper_id=None, change_time=change_time, status=status, baby_id=baby_id)
        diaper.validate_status()
        return self.diaper_repo.create_diaper(diaper)

    def get_diaper_by_baby_id(self, baby_id: int) -> list[Diaper]:
        if baby_id <=0:
            raise ValueError("Invalid baby id")

        baby = self.baby_repo.get_by_id(baby_id)
        if baby is None:
            raise ValueError("Baby id does not exist")

        return self.diaper_repo.get_by_baby_id(baby_id)

    def get_diaper_by_diaper_id(self, baby_id:int, diaper_id: int) -> Diaper|None:
        if diaper_id <= 0:
            raise ValueError("Invalid sleep id")
        if baby_id <= 0:
            raise ValueError("Invalid baby id")

        diaper = self.diaper_repo.get_by_diaper_id(diaper_id)
        if diaper is None:
            return None

        if diaper.baby_id != baby_id:
            raise PermissionError("Diaper does not belong to this baby")
        return diaper

    def update_diaper(self, baby_id: int, diaper_id: int, change_time: datetime,status: str) -> Diaper|None:
        if diaper_id <= 0 or baby_id <= 0:
            raise ValueError("Invalid id")
        if change_time > datetime.now(timezone.utc):
            raise ValueError("Change time cannot be in the future")

        diaper = self.diaper_repo.get_by_diaper_id(diaper_id)
        if diaper is None:
            return None

        if diaper.baby_id != baby_id:
            raise PermissionError("Diaper does not belong to this baby")

        diaper.change_time = change_time
        diaper.status = status
        diaper.validate_status()

        return self.diaper_repo.update_diaper(diaper)

    def delete_diaper_by_id(self, baby_id: int, diaper_id: int) -> Diaper|None:
        if baby_id <= 0 or diaper_id <= 0:
            raise ValueError("Invalid id")

        diaper = self.get_diaper_by_diaper_id(baby_id, diaper_id)
        if diaper is None:
            return None

        return self.diaper_repo.delete_diaper(diaper_id)
