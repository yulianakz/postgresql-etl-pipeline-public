from flask_app.db.repository_interfaces.user_repo_interface import UserRepository
from flask_app.domain.entities.user import User, Role

class UserService:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def create_user(self, user_name: str, password_hash: str, role:Role) -> User:
        user_name = user_name.strip().lower()
        if not (3<=len(user_name) <=50):
            raise ValueError("Invalid user name")

        check_username = self.repo.get_by_username(user_name)
        if check_username:
            raise ValueError("Username already exists")

        if not (50 <= len(password_hash) <= 255):
            raise ValueError("Invalid password")

        if not isinstance(role, Role):
            raise ValueError("Invalid role")

        user = User(user_id=None, user_name=user_name, password_hash=password_hash, role=role, created_at=None)
        return self.repo.create_user(user)

    def get_user_by_username(self, user_name: str) -> User|None:
        user_name = user_name.strip().lower()
        if not (3<=len(user_name) <=50):
            raise ValueError("Invalid user name")

        user = self.repo.get_by_username(user_name)
        if user is None:
            return None

        return user

    def get_user_by_id(self, user_id: int) -> User|None:
        if user_id <=0:
            raise ValueError("Invalid user id")

        user = self.repo.get_by_id(user_id)
        if user is None:
            return None

        return user

    def get_all_users(self) -> list[User]|None:
        return self.repo.get_all()







