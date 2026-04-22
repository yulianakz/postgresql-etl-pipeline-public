from abc import ABC, abstractmethod



class CoreRepositoryInterface(ABC):

    @abstractmethod
    def raw_sql_load(
            self,
            raw_sql: str,
            params: dict|None=None
    ) -> int | None:
        pass

    @abstractmethod
    def count_rows_by_job_id(
            self,
            table_name: str,
            job_id: int
    ) -> int | None:
        pass