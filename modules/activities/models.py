import uuid
from datetime import datetime, timezone

from models import db, BaseModel


ACTIVITY_TYPES = ['call', 'email', 'meeting', 'task', 'note']

# Outcomes vary by type, but we use a single set for simplicity.
ACTIVITY_OUTCOMES = [
    '', 'completed', 'no_answer', 'left_voicemail', 'connected',
    'replied', 'meeting_booked', 'bounced', 'opened', 'clicked',
    'converted', 'forwarded', 'cancelled',
]


class Activity(BaseModel):
    __tablename__ = 'activities'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = db.Column(db.String(20), default='task', index=True)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True, index=True)
    completed = db.Column(db.Boolean, default=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    outcome = db.Column(db.String(40), default='')
    owner = db.Column(db.String(120), nullable=True)

    deal_id = db.Column(db.String(36), db.ForeignKey('deals.id'), nullable=True, index=True)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=True, index=True)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=True, index=True)

    deal = db.relationship('Deal', backref='activities')
    contact = db.relationship('Contact', backref='activities')
    company = db.relationship('Company', backref='activities')

    def __repr__(self):
        return f'<Activity {self.type}:{self.subject}>'

    @property
    def is_overdue(self):
        if self.completed or self.due_date is None:
            return False
        # DB may return a naive datetime (SQLite text or Postgres without tz).
        # Strip tz from `now()` so the comparison works in both cases.
        now = datetime.now(timezone.utc)
        due = self.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        return due < now

    def to_dict(self):
        data = super().to_dict()
        data['is_overdue'] = self.is_overdue
        if self.deal:
            data['deal'] = {'id': self.deal.id, 'name': self.deal.name}
        else:
            data['deal'] = None
        if self.contact:
            data['contact'] = {'id': self.contact.id,
                               'full_name': self.contact.full_name()}
        else:
            data['contact'] = None
        if self.company:
            data['company'] = {'id': self.company.id, 'name': self.company.name}
        else:
            data['company'] = None
        return data
