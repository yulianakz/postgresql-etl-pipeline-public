from abc import ABC, abstractmethod
from flask_app.domain.entities.user import User


class UserRepository(ABC):

    @abstractmethod
    def create_user(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> User|None:
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> User|None:
        pass

    @abstractmethod
    def get_all(self):
        pass