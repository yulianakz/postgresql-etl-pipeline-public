from sqlalchemy.engine import Engine
from sqlalchemy import insert, select, update, delete, Table

from flask_app.domain.entities.diaper import Diaper
from flask_app.db.repository_interfaces.diaper_repo_interface import DiaperRepository
from flask_app.db.metadata import diaper_data


class PostgresDiaperRepository(DiaperRepository):

    TABLE = diaper_data

    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def _to_entity(row) -> Diaper:
        return Diaper(
            diaper_id=row["id"],
            change_time=row["change_time"],
            status=row["status"],
            baby_id=row["baby_id"])

    def create_diaper(self, diaper: Diaper) -> Diaper:

        stmt = (
            insert(self.TABLE)
            .values(
                change_time = diaper.change_time,
                status = diaper.status,
                baby_id = diaper.baby_id
            )
            .returning(
                self.TABLE.c.id,
                self.TABLE.c.change_time,
                self.TABLE.c.status,
                self.TABLE.c.baby_id
            )
        )

        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one()

        return self._to_entity(row)

    def get_by_baby_id(self, baby_id: int) -> list[Diaper]:

        stmt = (
            select(self.TABLE)
            .where(self.TABLE.c.baby_id == baby_id)
            .order_by(self.TABLE.c.id)
        )
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()

        return [self._to_entity(row) for row in rows]

    def get_by_diaper_id(self, diaper_id: int) -> Diaper | None:

        stmt = (
            select(self.TABLE)
            .where(self.TABLE.c.id == diaper_id)
        )

        with self.engine.connect() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)

    def update_diaper(self, diaper: Diaper) -> Diaper|None:

        stmt = (
            update(self.TABLE)
            .where(self.TABLE.c.id == diaper.id)
            .values(
                change_time = diaper.change_time,
                status = diaper.status
            )
            .returning(
                self.TABLE.c.id,
                self.TABLE.c.change_time,
                self.TABLE.c.status,
                self.TABLE.c.baby_id)
        )
        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)

    def delete_diaper(self, diaper_id) -> Diaper|None:

        stmt = (
            delete(self.TABLE)
            .where(self.TABLE.c.id == diaper_id)
            .returning(
                self.TABLE.c.id,
                self.TABLE.c.change_time,
                self.TABLE.c.status,
                self.TABLE.c.baby_id)
        )

        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)

