from sqlalchemy.engine import Engine
from sqlalchemy import insert, select

from flask_app.domain.entities.user import User
from flask_app.db.repository_interfaces.user_repo_interface import UserRepository
from flask_app.db.metadata import user_data

class PostgresUserRepository(UserRepository):

    TABLE = user_data

    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def _to_entity(row) -> User:
        return User(
            user_id=row["id"],
            user_name=row["user_name"],
            password_hash=row["password_hash"],
            role=row["role"],
            created_at=row["created_at"]
        )

    def create_user(self, user: User) -> User:

        stmt = (
            insert(self.TABLE)
            .values(
                user_name=user.user_name,
                password_hash=user.password_hash,
                role=user.role
            )
            .returning(
                self.TABLE.c.id,
                self.TABLE.c.user_name,
                self.TABLE.c.password_hash,
                self.TABLE.c.role,
                self.TABLE.c.created_at
            )
        )

        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one()

        return self._to_entity(row)

    def get_by_id(self, user_id: int) -> User|None:

        stmt = (
            select(self.TABLE)
            .where(self.TABLE.c.id == user_id)
        )

        with self.engine.connect() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)

    def get_by_username(self, user_name: str) -> User|None:

        stmt = (
            select(self.TABLE)
            .where(self.TABLE.c.user_name == user_name)
        )

        with self.engine.connect() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)

    def get_all(self) -> list[User]:

        stmt = (
            select(self.TABLE)
            .order_by(self.TABLE.c.id)
        )

        with self.engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()

        return [self._to_entity(row) for row in rows]
