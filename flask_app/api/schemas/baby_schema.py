from marshmallow import Schema, fields
from marshmallow_dataclass import class_schema
from dataclasses import dataclass

@dataclass
class BabyInput:
    name: str
    timezone: str

BabyInputSchema = class_schema(BabyInput)

class BabyListSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    timezone = fields.Str(dump_only=True)