"""Backup management for Contact Management System."""

import json
import shutil
import datetime
from pathlib import Path
from typing import List, Optional

from backend.database import store

BACKUP_DIR = Path("/home/jherney/futuristic-contact-manager/backups")
BACKUP_NAME = "contact_managers_backup_{date}"


def create_backup() -> Path:
    """Create a backup of all contact data."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{BACKUP_NAME}_{timestamp}"
    backup_path = BACKUP_DIR / backup_name
    
    # Create backup archive
    archive_path = BACKUP_DIR / f"{backup_name}.tar.gz"
    
    # Collect all contact data
    contacts = []
    for contact in store.contacts.values():
        contact_data = {
            "id": contact.id,
            "name": contact.name,
            "email": contact.email,
            "phone": contact.phone,
            "role": contact.role.value,
            "tags": contact.tags,
            "created_at": contact.created_at.isoformat() if contact.created_at else None,
            "updated_at": contact.updated_at.isoformat() if contact.updated_at else None,
            "attachments": contact.attachments,
            "audit_log": contact.audit_log
        }
        contacts.append(contact_data)
    
    # Write backup archive
    with open(archive_path, "wb") as f:
        shutil.make_archive(str(BACKUP_DIR / backup_name), "gztar", str(BACKUP_DIR / backup_name))
    
    # Also create JSON backup
    json_backup = BACKUP_DIR / f"{backup_name}.json"
    with open(json_backup, "w") as f:
        json.dump(contacts, f, indent=2)
    
    return backup_path


def list_backups() -> List[Path]:
    """List all available backups."""
    return sorted(BACKUP_DIR.glob("*.tar.gz")) + sorted(BACKUP_DIR.glob("*.json"))


def restore_backup(backup_path: Path) -> bool:
    """Restore contacts from a backup."""
    if not backup_path.exists():
        return False
    
    # Extract backup
    extract_dir = BACKUP_DIR / backup_path.stem.replace(".tar.gz", "") / backup_path.stem.replace(".json", "")
    extract_dir.mkdir(exist_ok=True)
    
    with open(backup_path, "rb") as f:
        shutil.unpack_archive(f, extract_dir)
    
    # Reload contacts from extracted data
    store.clear()  # Clear existing contacts
    for item in extract_dir.rglob("*.json"):
        if item.is_file():
            with open(item, "r") as f:
                contacts = json.load(f)
                for contact_data in contacts:
                    contact = Contact(
                        id=contact_data["id"],
                        name=contact_data["name"],
                        email=contact_data["email"],
                        phone=contact_data.get("phone"),
                        role=ContactRole(contact_data["role"]),
                        tags=contact_data.get("tags", []),
                        created_at=datetime.datetime.fromisoformat(contact_data["created_at"]) if contact_data.get("created_at") else None,
                        updated_at=datetime.datetime.fromisoformat(contact_data.get("updated_at")) if contact_data.get("updated_at") else None,
                        attachments=contact_data.get("attachments", []),
                        audit_log=contact_data.get("audit_log", [])
                    )
                    store.create(contact)
    
    return True
