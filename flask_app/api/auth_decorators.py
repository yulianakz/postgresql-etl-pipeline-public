from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt
from flask import abort
from flask_app.domain.entities.user import Role


def permission_manager(*allowed_roles):
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):

            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                abort(403, description="Forbidden: no permissions")

            return func(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(func):
    return permission_manager(Role.ADMIN.value)(func)

def all_roles_allowed(func):
    return permission_manager(Role.ADMIN.value, Role.GUEST.value)(func)
