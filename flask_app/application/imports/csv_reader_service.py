import csv
from typing import Iterator, Dict, Any


class CsvReader:

    @staticmethod
    def read_csv_by_row(filename: str) -> Iterator[Dict[str,Any]]:
        with open(filename, encoding="utf-8-sig", newline="") as f:
            yield from csv.DictReader(f)
