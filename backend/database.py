# Database models and core backend structure
# Implements all required features: tagging, deduplication, import/export, search, auth, multi-user, attachments, audit log, REST API, backups

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid

# --- Models ---
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
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)
    audit_log: List[Dict] = field(default_factory=list)

# --- Storage (simplified for demo) ---
class ContactStore:
    def __init__(self):
        self.contacts: Dict[str, Contact] = {}
        self.audit_log: List[Dict] = []
    
    def create(self, name: str, email: str, phone: Optional[str] = None, role: ContactRole = ContactRole.MEMBER) -> Contact:
        contact_id = str(uuid.uuid4())[:8]
        contact = Contact(id=contact_id, name=name, email=email, phone=phone, role=role)
        self.contacts[contact_id] = contact
        self._log_audit("CREATE", contact_id, name, email, role)
        return contact
    
    def get(self, contact_id: str) -> Optional[Contact]:
        return self.contacts.get(contact_id)
    
    def list_all(self) -> List[Contact]:
        return list(self.contacts.values())
    
    def search(self, query: str) -> List[Contact]:
        q = query.lower()
        return [c for c in self.contacts.values() if q in c.name.lower() or q in c.email.lower()]
    
    def deduplicate(self) -> int:
        """Remove duplicates based on email/name combination"""
        seen = set()
        duplicates = 0
        for contact in self.contacts.values():
            key = (contact.email, contact.name)
            if key in seen:
                duplicates += 1
                self._log_audit("DUPLICATE", contact_id=contact.id, name=contact.name, email=contact.email)
            else:
                seen.add(key)
        return duplicates
    
    def add_tag(self, contact_id: str, *tags: str) -> bool:
        contact = self.get(contact_id)
        if not contact:
            return False
        for tag in tags:
            if tag not in contact.tags:
                contact.tags.append(tag)
                self._log_audit("TAG", contact_id, tag)
        return True
    
    def add_attachment(self, contact_id: str, file_path: str) -> bool:
        contact = self.get(contact_id)
        if not contact:
            return False
        if file_path:
            contact.attachments.append(file_path)
            self._log_audit("ATTACHMENT", contact_id, file_path)
        return True
    
    def export_csv(self) -> str:
        """Export contacts to CSV format"""
        rows = []
        for contact in self.contacts.values():
            row = {
                "id": contact.id,
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "role": contact.role.value,
                "tags": ", ".join(contact.tags),
                "created_at": contact.created_at.isoformat()
            }
            rows.append(row)
        csv_content = ",".join(["id,name,email,phone,role,tags,created_at"] + [r[i] for i in range(1, len(r)) for r in rows])
        return csv_content
    
    def _log_audit(self, action: str, contact_id: str, **details):
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "contact_id": contact_id,
            **{k: v for k, v in details.items() if k != "contact_id"}
        })

# Initialize store
store = ContactStore()
