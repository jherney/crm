# User model for Contact Management System
# Extends Contact with additional authentication fields

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

class UserRole(Enum):
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"

@dataclass
class User:
    id: str
    username: str
    email: str
    role: UserRole = UserRole.MEMBER
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }
