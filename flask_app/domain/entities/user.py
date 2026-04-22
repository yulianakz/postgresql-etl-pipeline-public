from enum import Enum
from datetime import datetime

class Role(str, Enum):
    ADMIN = 'admin'
    GUEST = 'guest'

class User:

    def __init__(self, user_id: int|None, user_name: str, password_hash: str, role: Role, created_at: datetime|None):
        self.id = user_id
        self.user_name = user_name
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at