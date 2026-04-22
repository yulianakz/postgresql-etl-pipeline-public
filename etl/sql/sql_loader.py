import os

SQL_DIR = os.path.dirname(__file__)

def load_sql(relative_path: str) -> str:

    full_path = os.path.join(SQL_DIR, relative_path)

    with open(full_path, "r") as f:
        return f.read()