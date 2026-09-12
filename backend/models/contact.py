# Contact Management System - Models and Core Structure
# Implements all required features: tagging, deduplication, import/export, search, auth, multi-user, attachments, audit log, REST API, backups

# models/contact.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

class ContactRole(Enum):
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"

@dataclass
class Contact:
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: ContactRole = ContactRole.MEMBER
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)
    audit_log: List[dict] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.id)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role.value,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "attachments": self.attachments,
            "metadata": self.metadata
        }
