from flask import Flask
from flask_smorest import Api
from flask_jwt_extended import JWTManager

from flask_app.api.routes.sleep_api import sleep_tb_blp, BabySleepListRequests, SleepListRequests
from flask_app.api.routes.baby_api import baby_tb_blp, BabyListRequests, BabyByIdRequests
from flask_app.api.routes.diaper_api import diaper_tb_blp, DiaperListRequests, BabyDiaperListRequests
from flask_app.api.routes.auth_api import auth_blp, Login, Register, Refresh

from flask_app.db.engine import engine

from flask_app.application.services.baby_service import BabyService
from flask_app.application.services.sleep_service import SleepService
from flask_app.application.services.diaper_service import DiaperService
from flask_app.application.services.user_service import UserService
from flask_app.application.services.auth_service import AuthService

from flask_app.db.repositories.postgres_baby_repo import PostgresBabyRepository
from flask_app.db.repositories.postgres_sleep_repo import PostgresSleepRepository
from flask_app.db.repositories.postgres_diaper_repo import PostgresDiaperRepository
from flask_app.db.repositories.postgres_user_repo import PostgresUserRepository

import os
from datetime import timedelta

def create_app() -> Flask:
    app = Flask(__name__)

    app.config["API_TITLE"] = "Baby Sleep Data Project"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY must be set (e.g. in .env)")
    app.config["JWT_SECRET_KEY"] = jwt_secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=60)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]

    api = Api(app)
    jwt = JWTManager(app)

    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200

    baby_repo = PostgresBabyRepository(engine)
    sleep_repo = PostgresSleepRepository(engine)
    diaper_repo = PostgresDiaperRepository(engine)
    user_repo = PostgresUserRepository(engine)

    baby_service = BabyService(baby_repo)
    sleep_service = SleepService(sleep_repo, baby_repo)
    diaper_service = DiaperService(diaper_repo, baby_repo)
    user_service = UserService(user_repo)
    auth_service = AuthService(user_service)

    BabyListRequests.baby_service = baby_service
    BabyByIdRequests.baby_service = baby_service

    SleepListRequests.sleep_service = sleep_service
    BabySleepListRequests.sleep_service = sleep_service

    DiaperListRequests.diaper_service = diaper_service
    BabyDiaperListRequests.diaper_service = diaper_service

    Login.auth_service = auth_service
    Refresh.auth_service = auth_service
    Register.auth_service = auth_service

    api.register_blueprint(baby_tb_blp)
    api.register_blueprint(sleep_tb_blp)
    api.register_blueprint(diaper_tb_blp)
    api.register_blueprint(auth_blp)

    return app
