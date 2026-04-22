from marshmallow import Schema, fields
from marshmallow_dataclass import class_schema
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DiaperInput:
    change_time: datetime
    status: str

DiaperInputSchema = class_schema(DiaperInput)

class OutputDiaperSchema(Schema):
    baby_id = fields.Int(dump_only=True)
    id = fields.Int(dump_only=True)
    change_time = fields.DateTime(dump_only=True)
    status = fields.Str(dump_only=True)