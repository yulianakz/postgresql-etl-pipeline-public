from abc import ABC, abstractmethod
from flask_app.domain.entities.diaper import Diaper

class DiaperRepository(ABC):

    @abstractmethod
    def create_diaper(self, diaper: Diaper) -> Diaper:
        pass

    @abstractmethod
    def get_by_baby_id(self, baby_id: int) -> list[Diaper]:
        pass

    @abstractmethod
    def get_by_diaper_id(self, diaper_id: int) -> Diaper|None:
        pass

    @abstractmethod
    def update_diaper(self, diaper: Diaper) -> Diaper|None:
        pass

    @abstractmethod
    def delete_diaper(self, diaper_id: int) -> Diaper|None:
        pass