from datetime import datetime, timezone

from sqlalchemy import (
    Table, Column, Integer, String, ForeignKey, DateTime, Enum, Index
)
from flask_app.db.engine import metadata
from flask_app.domain.entities.user import Role

baby_info = Table(
    'baby_info',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String(50)),
    Column('timezone', String(50), nullable=False)
)

sleep_data = Table(
    'sleep_data',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sleep_start', DateTime(timezone=True), nullable=False),
    Column('sleep_duration', Integer, nullable=False),
    Column('baby_id', Integer, ForeignKey('baby_info.id'), nullable=False),
)

diaper_data = Table(
    'diaper_data',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('change_time', DateTime(timezone=True), nullable=False),
    Column('status', String, nullable=False),
    Column('baby_id', Integer, ForeignKey('baby_info.id'), nullable=False),
)

Index(
    'idx_sleep_data_baby_id',
    sleep_data.c.baby_id
)

Index(
    'idx_diaper_data_baby_id',
    diaper_data.c.baby_id
)

user_data = Table(
    'user_data',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_name', String(50), nullable=False, unique=True),
    Column('password_hash', String(255), nullable=False),
    Column('role', Enum(Role, name='user_role_enum'), nullable=False, default = Role.GUEST),
    Column('created_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)