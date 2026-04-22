from flask_smorest import Blueprint, abort
from flask.views import MethodView

from flask_app.application.services.auth_service import AuthService
from flask_app.api.schemas.auth_schema import *
from flask_app.domain.entities.user import Role

from flask_jwt_extended import jwt_required

auth_blp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_blp.route("/register")
class Register(MethodView):

    auth_service: AuthService = None

    @auth_blp.arguments(RegisterInputSchema)
    @auth_blp.response(201, UserOutputSchema)
    def post(self, data):
        try:
            return self.auth_service.register(data.user_name, data.password, Role.GUEST)
        except ValueError as e:
            abort(400, message=str(e))


@auth_blp.route("/login")
class Login(MethodView):

    auth_service: AuthService = None

    @auth_blp.arguments(LoginInputSchema)
    @auth_blp.response(200, TokenOutputSchema)
    def post(self, data):
        try:
            return self.auth_service.login(data.user_name, data.password)
        except ValueError as e:
            abort(400, message=str(e))


@auth_blp.route("/refresh")
class Refresh(MethodView):

    auth_service: AuthService = None

    @jwt_required(refresh=True)
    @auth_blp.response(200, RefreshOutputSchema)
    def post(self):
        try:
            return self.auth_service.refresh_access_token()
        except ValueError as e:
            abort(400, message=str(e))

