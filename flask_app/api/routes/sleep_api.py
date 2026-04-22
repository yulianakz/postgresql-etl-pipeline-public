from flask_smorest import Blueprint, abort
from flask.views import MethodView

from flask_app.application.services.sleep_service import SleepService
from flask_app.api.schemas.sleep_schema import *

from flask_app.api.auth_decorators import admin_required,all_roles_allowed


sleep_tb_blp = Blueprint("sleep_data", __name__, url_prefix="/", description="Operations on 'Sleep Data' Table")


@sleep_tb_blp.route("baby/<int:baby_id>/sleep")
class BabySleepListRequests(MethodView):

    sleep_service: SleepService = None

    #Get all sleeps per baby
    @sleep_tb_blp.response(200, OutputSleepSchema(many=True))
    @all_roles_allowed
    def get(self, baby_id):
        try:
            sleep_list = self.sleep_service.get_sleep_by_baby_id(baby_id)
            return sleep_list
        except ValueError as e:
            abort(400, message=str(e))


    #Create sleep row
    @sleep_tb_blp.arguments(SleepInputSchema)
    @sleep_tb_blp.response(201, OutputSleepSchema)
    @admin_required
    def post(self, data, baby_id):
        try:
            sleep = self.sleep_service.create_sleep(data.sleep_start, data.sleep_duration, baby_id)
            return sleep
        except ValueError as e:
            abort(400, message=str(e))


@sleep_tb_blp.route("baby/<int:baby_id>/sleep/<int:sleep_id>")
class SleepListRequests(MethodView):

    sleep_service: SleepService = None

    #get sleep by id and baby_id
    @sleep_tb_blp.response(200, OutputSleepSchema)
    @all_roles_allowed
    def get(self, baby_id, sleep_id):
        try:
            sleep = self.sleep_service.get_sleep_by_sleep_id(baby_id, sleep_id)
            if sleep is None:
                abort(404, message="Sleep not found")
            return sleep
        except ValueError as e:
            abort(400, message=str(e))
        except PermissionError as e:
            abort(403, message=str(e))


    # Update sleep by id
    @sleep_tb_blp.arguments(SleepInputSchema)
    @sleep_tb_blp.response(200, OutputSleepSchema)
    @admin_required
    def put(self, data, baby_id, sleep_id):
        try:
            updated_sleep = self.sleep_service.update_sleep(baby_id, sleep_id, data.sleep_start, data.sleep_duration)
            if updated_sleep is None:
                abort(404, message="Sleep not found")
            return updated_sleep
        except ValueError as e:
            abort(400, message=str(e))
        except PermissionError as e:
            abort(403, message=str(e))


    # Delete sleep by id
    @sleep_tb_blp.response(200, OutputSleepSchema)
    @admin_required
    def delete(self, baby_id, sleep_id):
        try:
            deleted_sleep = self.sleep_service.delete_sleep_by_id(baby_id, sleep_id)
            if deleted_sleep is None:
                abort(404, message="Sleep not found")
            return deleted_sleep
        except ValueError as e:
            abort(400, message=str(e))
        except PermissionError as e:
            abort(403, message=str(e))

