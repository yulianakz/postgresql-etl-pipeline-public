from marshmallow import Schema, fields
from marshmallow_dataclass import class_schema
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SleepInput:
    sleep_start: datetime
    sleep_duration: int

SleepInputSchema = class_schema(SleepInput)

class OutputSleepSchema(Schema):
    baby_id = fields.Int(dump_only=True)
    id = fields.Int(dump_only=True)
    start = fields.DateTime(dump_only=True)
    duration = fields.Int(dump_only=True)