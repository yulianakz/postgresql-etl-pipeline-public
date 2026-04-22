from flask_app.db.repository_interfaces.baby_repo_interface import BabyRepository
from flask_app.domain.entities.baby import Baby


class BabyService:

    def __init__(self, repo: BabyRepository):
        self.repo = repo

    def create_baby(self, name: str, timezone: str) -> Baby:
        name = name.strip()
        if not (3<=len(name) <=50):
            raise ValueError("Invalid baby name")

        baby = Baby(baby_id=None, name=name, timezone=timezone)
        baby.validate_timezone()
        return self.repo.create_baby(baby)

    def get_all_babies(self) -> list[Baby]:
        return self.repo.get_all()

    def get_baby_by_id(self, baby_id: int) -> Baby|None:
        if baby_id <=0:
            raise ValueError("Invalid baby id")
        baby = self.repo.get_by_id(baby_id)
        if baby is None:
            return None
        return baby


    def update_baby_info(self, baby_id: int, new_name: str, new_timezone: str) -> Baby|None:
        baby = self.get_baby_by_id(baby_id)
        if baby is None:
            return None

        new_name = new_name.strip()
        new_timezone = new_timezone.strip()
        if not (3 <= len(new_name) <= 50):
            raise ValueError("Invalid baby name")

        baby.name = new_name
        baby.timezone = new_timezone
        baby.validate_timezone()

        return self.repo.update_baby(baby)

    def delete_baby_by_id(self, baby_id: int) -> Baby|None:
        if baby_id <= 0:
            raise ValueError("Invalid baby id")
        return self.repo.delete_baby(baby_id)





