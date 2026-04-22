from flask_smorest import Blueprint, abort
from flask.views import MethodView

from flask_app.api.schemas.diaper_schema import *
from flask_app.application.services.diaper_service import DiaperService

from flask_app.api.auth_decorators import admin_required,all_roles_allowed

diaper_tb_blp = Blueprint("diaper_data", __name__, url_prefix="/", description="Operations on 'Diaper Data' Table")


@diaper_tb_blp.route("baby/<int:baby_id>/diaper")
class BabyDiaperListRequests(MethodView):

    diaper_service: DiaperService = None

    # Get all diaper data per baby
    @diaper_tb_blp.response(200, OutputDiaperSchema(many=True))
    @all_roles_allowed
    def get(self, baby_id):
        try:
            diaper_list = self.diaper_service.get_diaper_by_baby_id(baby_id)
            return diaper_list
        except ValueError as e:
            abort(400, message=str(e))


    # Create diaper row per baby
    @diaper_tb_blp.arguments(DiaperInputSchema)
    @diaper_tb_blp.response(201, OutputDiaperSchema)
    @admin_required
    def post(self, data, baby_id):
        try:
            diaper = self.diaper_service.create_diaper(data.change_time, data.status, baby_id)
            return diaper
        except ValueError as e:
            abort(400, message=str(e))



@diaper_tb_blp.route("baby/<int:baby_id>/diaper/<int:diaper_id>")
class DiaperListRequests(MethodView):

    diaper_service: DiaperService = None

    # get diaper data by id and baby_id
    @diaper_tb_blp.response(200, OutputDiaperSchema)
    @all_roles_allowed
    def get(self, baby_id, diaper_id):
        try:
            diaper = self.diaper_service.get_diaper_by_diaper_id(baby_id, diaper_id)
            if diaper is None:
                abort(404, message="Sleep not found")
            return diaper
        except ValueError as e:
            abort(400, message=str(e))
        except PermissionError as e:
            abort(403, message=str(e))


    # Update diaper by id per baby
    @diaper_tb_blp.arguments(DiaperInputSchema)
    @diaper_tb_blp.response(200, OutputDiaperSchema)
    @admin_required
    def put(self, data, baby_id, diaper_id):
        try:
            updated_diaper = self.diaper_service.update_diaper(baby_id, diaper_id, data.change_time, data.status)
            if updated_diaper is None:
                abort(404, message="Diaper data not found")
            return updated_diaper
        except ValueError as e:
            abort(400, message=str(e))
        except PermissionError as e:
            abort(403, message=str(e))


    # Delete sleep by id
    @diaper_tb_blp.response(200, OutputDiaperSchema)
    @admin_required
    def delete(self, baby_id, diaper_id):
        try:
            deleted_diaper = self.diaper_service.delete_diaper_by_id(baby_id, diaper_id)
            if deleted_diaper is None:
                abort(404, message="Diaper not found")
            return deleted_diaper
        except ValueError as e:
            abort(400, message=str(e))
        except PermissionError as e:
            abort(403, message=str(e))