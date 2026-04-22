from sqlalchemy.engine import Engine
from sqlalchemy import insert, select, update, delete,Table

from flask_app.domain.entities.baby import Baby
from flask_app.db.repository_interfaces.baby_repo_interface import BabyRepository
from flask_app.db.metadata import baby_info


class PostgresBabyRepository(BabyRepository):

    TABLE = baby_info

    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def _to_entity(row) -> Baby:
        return Baby(baby_id=row["id"], name=row["name"], timezone=row["timezone"])

    def create_baby(self, baby: Baby) -> Baby:

        stmt = (
            insert(self.TABLE)
            .values(name=baby.name, timezone=baby.timezone)
            .returning(
               self.TABLE.c.id,
               self.TABLE.c.name,
               self.TABLE.c.timezone)
        )
        with self.engine.begin() as conn:
          row = conn.execute(stmt).mappings().one()

        return self._to_entity(row)


    def get_all(self) -> list[Baby]:

        stmt = (
            select(self.TABLE)
            .order_by(self.TABLE.c.id)
        )
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()

        return [self._to_entity(row) for row in rows]


    def get_by_id(self, baby_id: int) -> Baby|None:

        stmt = (
            select(self.TABLE)
            .where(self.TABLE.c.id == baby_id)
        )
        with self.engine.connect() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)


    def update_baby(self, baby: Baby) -> Baby|None:

        stmt = (
            update(self.TABLE)
            .where(self.TABLE.c.id == baby.id)
            .values(name = baby.name, timezone=baby.timezone)
            .returning(
                self.TABLE.c.id,
                self.TABLE.c.name,
                self.TABLE.c.timezone)
        )
        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)


    def delete_baby(self, baby_id: int) -> Baby|None:

        stmt = (
            delete(self.TABLE)
            .where(self.TABLE.c.id == baby_id)
            .returning(
                self.TABLE.c.id,
                self.TABLE.c.name,
                self.TABLE.c.timezone)
        )

        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)
