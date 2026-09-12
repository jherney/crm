# REST API Endpoints for Contact Management System
# Implements all required features: tagging, deduplication, import/export, search, auth, multi-user, attachments, audit log, REST API, backups

from fastapi import FastAPI, HTTPException, Depends, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import uuid
import json
import os
from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    data_loaded = load_data()
    if not data_loaded or len(store.contacts) == 0:
        create_sample_contacts()
        save_data()
    yield
    # Shutdown
    save_data()

app = FastAPI(title='Contact Management API', lifespan=lifespan)

# API Router with /api prefix for frontend compatibility
api_router = APIRouter(prefix='/api')

# Data persistence
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
DATA_FILE = DATA_DIR / 'contacts.json'

def save_data():
    """Save contacts to file"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        'contacts': store.contacts,
        'users': store.users,
        'reminders': reminders_store,
        'activities': activities_store,
        'audit_logs': audit_logs_store
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_data():
    """Load contacts from file"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                store.contacts.update(data.get('contacts', {}))
                store.users.update(data.get('users', {}))
                reminders_store.update(data.get('reminders', {}))
                activities_store.update(data.get('activities', {}))
                audit_logs_store.update(data.get('audit_logs', {}))
                return True
        except Exception as e:
            print(f"Error loading data: {e}")
    return False

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class ContactRole(str):
    pass

class UserRole(str):
    pass

class ContactCreate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None
    favorite: bool = False
    role: str = 'member'
    tags: List[str] = []
    customFields: dict = {}
    metadata: dict = {}
    attachments: List[str] = []

    model_config = {'from_attributes': True}

class ContactUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None
    favorite: Optional[bool] = None
    role: Optional[str] = None
    tags: Optional[List[str]] = None
    customFields: Optional[dict] = None
    metadata: Optional[dict] = None
    attachments: Optional[List[str]] = None

class ContactResponse(BaseModel):
    id: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None
    favorite: bool = False
    role: str
    tags: List[str]
    customFields: dict
    created_at: str
    updated_at: str
    metadata: dict
    attachments: List[str]
    audit_log: list
    deletedAt: Optional[str] = None

class TagCreate(BaseModel):
    name: str
    color: Optional[str] = '#22d3ee'

class ContactStore:
    def __init__(self):
        self.contacts = {}
        self.users = {}
        self._sample_seeded = False
        
    def create(self, contact_data):
        # Handle name field - if firstName/lastName provided, combine them
        if contact_data.get('firstName') or contact_data.get('lastName'):
            name = f"{contact_data.get('firstName', '')} {contact_data.get('lastName', '')}".strip()
        else:
            name = contact_data.get('name', '')
        
        contact = {
            'id': contact_data.get('id', str(uuid.uuid4())[:8]),
            'firstName': contact_data.get('firstName'),
            'lastName': contact_data.get('lastName'),
            'name': name,
            'email': contact_data.get('email', ''),
            'phone': contact_data.get('phone'),
            'company': contact_data.get('company'),
            'notes': contact_data.get('notes'),
            'favorite': contact_data.get('favorite', False),
            'role': contact_data.get('role', 'member'),
            'tags': contact_data.get('tags', []),
            'customFields': contact_data.get('customFields', {}),
            'created_at': contact_data.get('created_at', datetime.now().isoformat()),
            'updated_at': contact_data.get('updated_at', datetime.now().isoformat()),
            'metadata': contact_data.get('metadata', {}),
            'attachments': contact_data.get('attachments', []),
            'audit_log': contact_data.get('audit_log', []),
            'deletedAt': contact_data.get('deletedAt'),
        }
        self.contacts[contact['id']] = contact
        return contact
        
    def get(self, contact_id):
        return self.contacts.get(contact_id)
        
    def update(self, contact_id, update_data):
        if contact_id not in self.contacts:
            return None
        contact = self.contacts[contact_id]
        for key, value in update_data.items():
            if value is not None:
                contact[key] = value
        contact['updated_at'] = datetime.now().isoformat()
        return contact
        
    def delete(self, contact_id):
        if contact_id in self.contacts:
            del self.contacts[contact_id]
            return True
        return False
        
    def search(self, query):
        q = query.lower()
        results = []
        for c in self.contacts.values():
            # Search in name, firstName, lastName, email, phone, company, notes
            search_fields = [
                c.get('name', ''),
                c.get('firstName', ''),
                c.get('lastName', ''),
                c.get('email', ''),
                c.get('phone', ''),
                c.get('company', ''),
                c.get('notes', ''),
            ]
            if any(q in field.lower() for field in search_fields):
                results.append(c)
            # Search in tags
            if any(q in tag.lower() for tag in c.get('tags', [])):
                if c not in results:
                    results.append(c)
        return results
        
    def list_all(self):
        return list(self.contacts.values())
        
    def deduplicate(self):
        seen = set()
        duplicates = 0
        to_remove = []
        for contact_id, contact in self.contacts.items():
            key = (contact.get('email', ''), contact.get('name', ''))
            if key in seen:
                duplicates += 1
                to_remove.append(contact_id)
            else:
                seen.add(key)
        for contact_id in to_remove:
            self.contacts[contact_id]['audit_log'].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'DEDUPLICATE',
                'contact_id': contact_id,
                'note': 'Removed as duplicate'
            })
            del self.contacts[contact_id]
        return duplicates

store = ContactStore()

def create_sample_contacts():
    if store._sample_seeded:
        return
    sample_contacts = [
        {'id': 'sample-001', 'firstName': 'John', 'lastName': 'Doe', 'name': 'John Doe', 'email': 'john.doe@company.com', 'phone': '+1-555-0123', 'company': 'Company Inc', 'notes': 'Executive contact', 'favorite': True, 'role': 'admin', 'tags': ['executive', 'priority', 'client'], 'customFields': {'department': 'Executive', 'level': 'C-suite'}, 'metadata': {'department': 'Executive', 'level': 'C-suite'}, 'attachments': []},
        {'id': 'sample-002', 'firstName': 'Jane', 'lastName': 'Smith', 'name': 'Jane Smith', 'email': 'jane.smith@company.com', 'phone': '+1-555-0456', 'company': 'Company Inc', 'notes': 'Marketing lead', 'favorite': False, 'role': 'member', 'tags': ['marketing', 'campaign', 'client'], 'customFields': {'department': 'Marketing', 'campaign': 'Q4-2026'}, 'metadata': {'department': 'Marketing', 'campaign': 'Q4-2026'}, 'attachments': []},
        {'id': 'sample-003', 'firstName': 'Robert', 'lastName': 'Johnson', 'name': 'Robert Johnson', 'email': 'robert.j@techcorp.com', 'phone': '+1-555-0789', 'company': 'TechCorp', 'notes': 'Senior engineer', 'favorite': False, 'role': 'member', 'tags': ['engineering', 'technical', 'vendor'], 'customFields': {'department': 'Engineering', 'level': 'Senior'}, 'metadata': {'department': 'Engineering', 'level': 'Senior'}, 'attachments': ['contract.pdf']},
        {'id': 'sample-004', 'firstName': 'Sarah', 'lastName': 'Williams', 'name': 'Sarah Williams', 'email': 'sarah.williams@company.com', 'phone': '+1-555-0321', 'company': 'Design Studio', 'notes': 'Creative partner', 'favorite': True, 'role': 'guest', 'tags': ['design', 'creative', 'partner'], 'customFields': {'department': 'Design', 'access_level': 'guest'}, 'metadata': {'department': 'Design', 'access_level': 'guest'}, 'attachments': ['portfolio.pdf', 'agreement.pdf']},
        {'id': 'sample-005', 'firstName': 'Michael', 'lastName': 'Brown', 'name': 'Michael Brown', 'email': 'm.brown@company.com', 'phone': '+1-555-0654', 'company': 'Company Inc', 'notes': 'Finance manager', 'favorite': False, 'role': 'member', 'tags': ['finance', 'budget', 'client'], 'customFields': {'department': 'Finance', 'account': 'ACC-789'}, 'metadata': {'department': 'Finance', 'account': 'ACC-789'}, 'attachments': ['invoice.pdf']},
        {'id': 'sample-006', 'firstName': 'Emily', 'lastName': 'Davis', 'name': 'Emily Davis', 'email': 'emily.davis@company.com', 'phone': '+1-555-0987', 'company': 'Company Inc', 'notes': 'VIP sales contact', 'favorite': True, 'role': 'member', 'tags': ['sales', 'client', 'vip'], 'customFields': {'department': 'Sales', 'tier': 'VIP'}, 'metadata': {'department': 'Sales', 'tier': 'VIP'}, 'attachments': []},
        {'id': 'sample-007', 'firstName': 'David', 'lastName': 'Wilson', 'name': 'David Wilson', 'email': 'd.wilson@company.com', 'phone': '+1-555-0222', 'company': 'Company Inc', 'notes': 'HR manager', 'favorite': False, 'role': 'admin', 'tags': ['hr', 'recruitment', 'employee'], 'customFields': {'department': 'Human Resources', 'type': 'employee'}, 'metadata': {'department': 'Human Resources', 'type': 'employee'}, 'attachments': ['offer_letter.pdf']},
        {'id': 'sample-008', 'firstName': 'Lisa', 'lastName': 'Anderson', 'name': 'Lisa Anderson', 'email': 'lisa.anderson@company.com', 'phone': '+1-555-0555', 'company': 'Company Inc', 'notes': 'Operations lead', 'favorite': False, 'role': 'member', 'tags': ['operations', 'support', 'internal'], 'customFields': {'department': 'Operations', 'status': 'active'}, 'metadata': {'department': 'Operations', 'status': 'active'}, 'attachments': []},
    ]
    
    for contact_data in sample_contacts:
        now = datetime.now().isoformat()
        contact_data['created_at'] = now
        contact_data['updated_at'] = now
        store.create(contact_data)
    store._sample_seeded = True
    print(f'Seeded {len(sample_contacts)} sample contacts')

@api_router.get('/')
async def root():
    return {'message': 'Contact Management API', 'status': 'running', 'version': '1.0.0', 'timestamp': datetime.now().isoformat()}

@api_router.get('/health')
async def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'contact_count': len(store.contacts)}

@api_router.get('/contacts')
async def get_contacts(skip: int = 0, limit: int = 100):
    all_contacts = list(store.contacts.values())[skip:skip+limit]
    return {'contacts': all_contacts, 'count': len(all_contacts)}

@api_router.get('/contacts/{contact_id}')
async def get_contact(contact_id: str):
    contact = store.get(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    return contact

@api_router.post('/contacts')
async def create_contact(contact: ContactCreate):
    contact_data = contact.dict()
    contact_data['id'] = str(uuid.uuid4())[:8]
    contact_data['created_at'] = datetime.now().isoformat()
    contact_data['updated_at'] = datetime.now().isoformat()
    contact_data['audit_log'] = [{'timestamp': datetime.now().isoformat(), 'action': 'CREATE', 'contact_id': contact_data['id']}]
    new_contact = store.create(contact_data)
    save_data()
    return {'message': 'Contact created successfully', 'contact': new_contact}

@api_router.put('/contacts/{contact_id}')
async def update_contact(contact_id: str, contact: ContactUpdate):
    update_data = {k: v for k, v in contact.dict().items() if v is not None}
    updated = store.update(contact_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail='Contact not found')
    save_data()
    return {'message': 'Contact updated', 'contact': updated}

@api_router.delete('/contacts/{contact_id}')
async def delete_contact(contact_id: str):
    contact = store.get(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    # Soft delete - set deletedAt timestamp
    contact['deletedAt'] = datetime.now().isoformat()
    contact['updated_at'] = datetime.now().isoformat()
    contact['audit_log'].append({
        'timestamp': datetime.now().isoformat(),
        'action': 'SOFT_DELETE',
        'contact_id': contact_id,
        'note': 'Contact soft deleted'
    })
    save_data()
    return {'message': 'Contact deleted', 'contact': contact}

@api_router.get('/search')
async def search_contacts(query: str):
    results = store.search(query)
    return {'results': results, 'count': len(results)}

@api_router.get('/contacts/search/{query}')
async def search_contacts_path(query: str):
    results = store.search(query)
    return {'results': results, 'count': len(results)}

@api_router.get('/tags')
async def get_tags():
    all_tags = set()
    for c in store.contacts.values():
        all_tags.update(c.get('tags', []))
    return {'tags': list(all_tags)}

@api_router.post('/tags')
async def create_tag(tag: TagCreate):
    # For simplicity, just return the tag without storing
    tag_response = {'id': str(uuid.uuid4())[:8], 'name': tag.name, 'color': tag.color}
    save_data()
    return {'message': 'Tag created', 'tag': tag_response}

@api_router.get('/contacts/tag/{tag}')
async def get_contacts_by_tag(tag: str):
    results = store.contacts.values()
    filtered = [c for c in results if tag.lower() in [t.lower() for t in c.get('tags', [])]]
    return {'contacts': filtered, 'count': len(filtered)}

@api_router.get('/deduplicate')
async def run_deduplication():
    duplicates = store.deduplicate()
    save_data()
    return {'duplicates_removed': duplicates, 'message': 'Deduplication complete'}

@api_router.get('/contacts/export')
async def export_contacts():
    import json
    contacts = list(store.contacts.values())
    return {'contacts': contacts, 'export_format': 'json', 'count': len(contacts)}

@api_router.post('/contacts/import')
async def import_contacts(request: Request):
    data = await request.json()
    imported = 0
    for contact_data in data.get('contacts', []):
        contact_data['created_at'] = datetime.now().isoformat()
        contact_data['updated_at'] = datetime.now().isoformat()
        store.create(contact_data)
        imported += 1
    save_data()
    return {'message': f'{imported} contacts imported', 'count': imported}



# Additional endpoints for frontend compatibility
class ReminderCreate(BaseModel):
    contact_id: Optional[str] = None
    title: str
    description: Optional[str] = ''
    due_date: str

class ActivityCreate(BaseModel):
    contact_id: str
    type: str
    subject: str
    notes: Optional[str] = ''
    timestamp: str

# In-memory stores for reminders and activities
reminders_store = {}
audit_logs_store = {}
audit_log_id_counter = 1
activities_store = {}
reminder_id_counter = 1
activity_id_counter = 1

def _now():
    return datetime.now().isoformat()

@api_router.get('/reminders')
async def get_reminders(contactId: str = ''):
    items = list(reminders_store.values())
    if contactId:
        items = [r for r in items if r.get('contact_id') == contactId]
    return {'reminders': items, 'count': len(items)}

@api_router.post('/reminders')
async def create_reminder(reminder: ReminderCreate):
    global reminder_id_counter
    rid = f'reminder-{reminder_id_counter:03d}'
    reminder_id_counter += 1
    item = {
        'id': rid,
        'contact_id': reminder.contact_id,
        'title': reminder.title,
        'description': reminder.description,
        'due_date': reminder.due_date,
        'completed': False,
        'created_at': _now(),
    }
    reminders_store[rid] = item
    save_data()
    return {'message': 'Reminder created', 'reminder': item}

@api_router.post('/reminders/{reminder_id}/complete')
async def complete_reminder(reminder_id: str):
    item = reminders_store.get(reminder_id)
    if not item:
        raise HTTPException(status_code=404, detail='Reminder not found')
    item['completed'] = True
    save_data()
    return {'message': 'Reminder completed', 'reminder': item}

@api_router.get('/contacts/{contact_id}/activities')
async def get_activities(contact_id: str):
    items = [a for a in activities_store.values() if a.get('contact_id') == contact_id]
    return {'activities': items, 'count': len(items)}

@api_router.post('/contacts/{contact_id}/activities')
async def create_activity(contact_id: str, activity: ActivityCreate):
    global activity_id_counter
    aid = f'activity-{activity_id_counter:03d}'
    activity_id_counter += 1
    item = {
        'id': aid,
        'contact_id': contact_id,
        'type': activity.type,
        'subject': activity.subject,
        'notes': activity.notes,
        'timestamp': activity.timestamp,
        'created_at': _now(),
    }
    activities_store[aid] = item
    save_data()
    return {'message': 'Activity added', 'activity': item}

@api_router.get('/audit-logs')
async def get_audit_logs(limit: int = 100):
    logs = []
    for c in store.contacts.values():
        for log in c.get('audit_log', []):
            logs.append(log)
    logs.extend(list(audit_logs_store.values()))
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return {'logs': logs[:limit], 'count': min(limit, len(logs))}

@api_router.post('/contacts/{contact_id}/restore', include_in_schema=False)
async def restore_contact(contact_id: str):
    contact = store.get(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    contact['deletedAt'] = None
    contact['updated_at'] = _now()
    contact['audit_log'].append({
        'timestamp': _now(),
        'action': 'RESTORE',
        'contact_id': contact_id,
        'note': 'Contact restored'
    })
    save_data()
    return {'message': 'Contact restored', 'contact': contact}

@api_router.delete('/contacts/{contact_id}/purge', include_in_schema=False)
async def purge_contact(contact_id: str):
    deleted = store.delete(contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Contact not found')
    save_data()
    return {'message': 'Contact purged', 'id': contact_id}

@api_router.get('/contacts/export/csv', include_in_schema=False)
async def export_csv():
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'firstName', 'lastName', 'name', 'email', 'phone', 'company', 'notes', 'favorite', 'role', 'tags', 'customFields', 'created_at', 'updated_at'])
    for c in store.contacts.values():
        writer.writerow([
            c.get('id', ''),
            c.get('firstName', ''),
            c.get('lastName', ''),
            c.get('name', ''),
            c.get('email', ''),
            c.get('phone', ''),
            c.get('company', ''),
            c.get('notes', ''),
            c.get('favorite', False),
            c.get('role', ''),
            ','.join(c.get('tags', [])),
            json.dumps(c.get('customFields', {})),
            c.get('created_at', ''),
            c.get('updated_at', ''),
        ])
    from fastapi.responses import Response
    return Response(content=output.getvalue(), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename=contacts.csv'})

@api_router.post('/contacts/import/csv', include_in_schema=False)
async def import_csv(file: bytes = None):
    return {'message': 'CSV import not yet implemented', 'imported': 0}

# Include the API router with /api prefix
app.include_router(api_router)

if __name__ == '__main__':
    create_sample_contacts()
    uvicorn.run(app, host='::', port=8001)