from abc import ABC, abstractmethod
from flask_app.domain.entities.sleep import Sleep

class SleepRepository(ABC):

    @abstractmethod
    def create_sleep(self, sleep: Sleep) -> Sleep:
        pass

    @abstractmethod
    def get_by_baby_id(self, baby_id: int) -> list[Sleep]:
        pass

    @abstractmethod
    def get_by_sleep_id(self, sleep_id: int) -> Sleep|None:
        pass

    @abstractmethod
    def update_sleep(self, sleep: Sleep) -> Sleep|None:
        pass

    @abstractmethod
    def delete_sleep(self, sleep_id: int) -> Sleep|None:
        pass