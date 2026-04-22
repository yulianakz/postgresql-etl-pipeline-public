from abc import ABC
from dataclasses import dataclass, fields
import hashlib


META_FIELDS = {"job_id", "row_hash", "loaded_at"}


@dataclass
class BaseEntity(ABC):

    row_hash: str | None = None

    def __post_init__(self):
        if self.row_hash is None:
            self.row_hash = self._compute_row_hash()

    def _compute_row_hash(self) -> str:
        """SHA-256 of business fields in dataclass declaration order (META_FIELDS excluded).

        Reordering or renaming fields in a subclass changes the hash for otherwise identical
        data. ``None`` becomes the five-character string from ``str(None)``, same as a stored
        value of that text would produce (rare collision to be aware of).
        """

        business_values = [
            str(getattr(self, f.name))
            for f in fields(self)
            if f.name not in META_FIELDS
        ]

        raw = "|".join(business_values)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()