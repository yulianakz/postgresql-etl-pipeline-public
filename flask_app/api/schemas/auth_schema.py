from marshmallow import Schema, fields
from marshmallow_dataclass import class_schema
from dataclasses import dataclass, field
from flask_app.domain.entities.user import Role

@dataclass
class RegisterSchema:
    user_name: str
    password: str = field(metadata={"marshmallow_field": fields.Str(load_only=True)})

RegisterInputSchema = class_schema(RegisterSchema)

class UserOutputSchema(Schema):
    id = fields.Int(dump_only=True)
    user_name = fields.Str(dump_only=True)
    role = fields.Enum(Role, by_value=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)

@dataclass
class LoginSchema:
    user_name: str
    password: str = field(metadata={"marshmallow_field": fields.Str(load_only=True)})

LoginInputSchema = class_schema(LoginSchema)

class TokenOutputSchema(Schema):
    access_token = fields.Str(dump_only=True)
    refresh_token = fields.Str(dump_only=True)

class RefreshOutputSchema(Schema):
    access_token = fields.Str(dump_only=True)
