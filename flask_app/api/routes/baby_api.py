from flask_smorest import Blueprint, abort
from flask.views import MethodView

from flask_app.application.services.baby_service import BabyService
from flask_app.api.schemas.baby_schema import *

from flask_app.api.auth_decorators import admin_required,all_roles_allowed


baby_tb_blp = Blueprint("baby_info", __name__, url_prefix="/baby", description="Operations on 'Baby Info' Table")


@baby_tb_blp.route("/")
class BabyListRequests(MethodView):

    #class attribute with a type annotation
    baby_service: BabyService = None

    # Get all babies
    @baby_tb_blp.response(200, BabyListSchema(many=True))
    @all_roles_allowed
    def get(self):
        babies_list = self.baby_service.get_all_babies()
        return babies_list

    #Create a new baby
    @baby_tb_blp.arguments(BabyInputSchema)
    @baby_tb_blp.response(201, BabyListSchema)
    @admin_required
    def post(self, data):
        try:
            baby = self.baby_service.create_baby(data.name, data.timezone)
            return baby
        except ValueError as e:
            abort(400, message=str(e))


@baby_tb_blp.route("/<int:baby_id>")
class BabyByIdRequests(MethodView):

    baby_service: BabyService = None

    # Get baby by id
    @baby_tb_blp.response(200, BabyListSchema)
    @all_roles_allowed
    def get(self, baby_id):
        try:
            baby = self.baby_service.get_baby_by_id(baby_id)
            if baby is None:
                abort(404, message="Baby not found")
            return baby
        except ValueError as e:
            abort(400, message=str(e))


    # Update baby by id
    @baby_tb_blp.arguments(BabyInputSchema)
    @baby_tb_blp.response(200, BabyListSchema)
    @admin_required
    def put(self, data, baby_id):
        try:
            updated_baby = self.baby_service.update_baby_info(baby_id, data.name, data.timezone)
            if updated_baby is None:
                abort(404, message="Baby not found")
            return updated_baby
        except ValueError as e:
            abort(400, message=str(e))

    # Delete baby by id
    @baby_tb_blp.response(200, BabyListSchema)
    @admin_required
    def delete(self, baby_id):
        try:
            deleted_baby = self.baby_service.delete_baby_by_id(baby_id)
            if deleted_baby is None:
                abort(404, message="Baby not found")
            return deleted_baby
        except ValueError as e:
            abort(400, message=str(e))
