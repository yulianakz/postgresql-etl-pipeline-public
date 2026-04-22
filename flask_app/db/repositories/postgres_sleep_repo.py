from sqlalchemy.engine import Engine
from sqlalchemy import insert, select, update, delete, Table

from flask_app.domain.entities.sleep import Sleep
from flask_app.db.repository_interfaces.sleep_repo_interface import SleepRepository
from flask_app.db.metadata import sleep_data

class PostgresSleepRepository(SleepRepository):

    TABLE = sleep_data

    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def _to_entity(row) -> Sleep:
        return Sleep(
            sleep_id=row["id"],
            sleep_start=row["sleep_start"],
            sleep_duration=row["sleep_duration"],
            baby_id = row["baby_id"])

    def get_by_baby_id(self, baby_id: int) -> list[Sleep]:

        stmt = (
            select(self.TABLE)
            .where(self.TABLE.c.baby_id == baby_id)
            .order_by(self.TABLE.c.id)
        )
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()

        return [self._to_entity(row) for row in rows]


    def create_sleep(self, sleep: Sleep) -> Sleep:

        stmt = (
             insert(self.TABLE)
            .values(
                sleep_start = sleep.start,
                sleep_duration = sleep.duration,
                baby_id = sleep.baby_id
            )
            .returning(
                 self.TABLE.c.id,
                 self.TABLE.c.sleep_start,
                 self.TABLE.c.sleep_duration,
                 self.TABLE.c.baby_id
            )
        )

        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one()

        return self._to_entity(row)


    def get_by_sleep_id(self, sleep_id: int) -> Sleep|None:

        stmt = (
            select(self.TABLE)
            .where(self.TABLE.c.id == sleep_id)
        )

        with self.engine.connect() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)


    def update_sleep(self, sleep: Sleep) -> Sleep|None:

        stmt = (
            update(self.TABLE)
            .where(self.TABLE.c.id == sleep.id)
            .values(
                sleep_start = sleep.start,
                sleep_duration = sleep.duration
            )
            .returning(
                self.TABLE.c.id,
                self.TABLE.c.sleep_start,
                self.TABLE.c.sleep_duration,
                self.TABLE.c.baby_id)
        )
        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)


    def delete_sleep(self, sleep_id) -> Sleep|None:

        stmt = (
            delete(self.TABLE)
            .where(self.TABLE.c.id == sleep_id)
            .returning(
                self.TABLE.c.id,
                self.TABLE.c.sleep_start,
                self.TABLE.c.sleep_duration,
                self.TABLE.c.baby_id)
        )

        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return self._to_entity(row)
