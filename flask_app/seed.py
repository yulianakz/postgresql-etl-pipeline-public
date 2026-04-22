import os
from pathlib import Path

from dotenv import load_dotenv

from flask_app.application.imports.csv_initial_import_service import CsvInitialImportService
from flask_app.application.services.auth_service import AuthService
from flask_app.application.services.baby_service import BabyService
from flask_app.application.services.diaper_service import DiaperService
from flask_app.application.services.sleep_service import SleepService
from flask_app.application.services.user_service import UserService
from flask_app.db.engine import engine, init_db
from flask_app.db.repositories.postgres_baby_repo import PostgresBabyRepository
from flask_app.db.repositories.postgres_diaper_repo import PostgresDiaperRepository
from flask_app.db.repositories.postgres_sleep_repo import PostgresSleepRepository
from flask_app.db.repositories.postgres_user_repo import PostgresUserRepository
from flask_app.domain.entities.user import Role
from flask_app.logging_config import configure_logging


ROOT_DIR = Path(__file__).resolve().parent.parent
FLAG_FILE = ROOT_DIR / "flask_app" / "data_files" / "_initial_load_done.txt"


def run_seed() -> None:
    load_dotenv(ROOT_DIR / ".env")
    configure_logging()
    init_db()

    baby_repo = PostgresBabyRepository(engine)
    sleep_repo = PostgresSleepRepository(engine)
    diaper_repo = PostgresDiaperRepository(engine)
    user_repo = PostgresUserRepository(engine)

    baby_service = BabyService(baby_repo)
    sleep_service = SleepService(sleep_repo, baby_repo)
    diaper_service = DiaperService(diaper_repo, baby_repo)
    user_service = UserService(user_repo)
    auth_service = AuthService(user_service)

    importer = CsvInitialImportService(
        baby_service=baby_service,
        sleep_service=sleep_service,
        diaper_service=diaper_service,
    )

    if not FLAG_FILE.exists():
        importer.import_all_for_baby(
            baby_name="Adriana",
            tz="Europe/Chisinau",
            sleep_csv="flask_app/data_files/sleep_data.csv",
            diaper_csv="flask_app/data_files/diaper_data.csv",
        )
        FLAG_FILE.touch()

    bootstrap_user = os.getenv("BOOTSTRAP_ADMIN_USERNAME")
    bootstrap_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")

    if bootstrap_user and bootstrap_password:
        existing_user = user_service.get_user_by_username(bootstrap_user)
        if not existing_user:
            auth_service.register(bootstrap_user, bootstrap_password, Role.ADMIN)


if __name__ == "__main__":
    run_seed()
