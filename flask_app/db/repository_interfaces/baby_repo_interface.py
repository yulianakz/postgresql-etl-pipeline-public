from abc import ABC, abstractmethod
from flask_app.domain.entities.baby import Baby


class BabyRepository(ABC):

    @abstractmethod
    def create_baby(self, baby: Baby) -> Baby:
        pass

    @abstractmethod
    def get_by_id(self, baby_id: int) -> Baby|None:
        pass

    @abstractmethod
    def get_all(self) -> list[Baby]:
        pass

    @abstractmethod
    def update_baby(self, baby: Baby) -> Baby|None:
        pass

    @abstractmethod
    def delete_baby(self, baby_id: int) -> Baby|None:
        pass
