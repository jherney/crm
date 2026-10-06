import uuid

from models import db, BaseModel


EVENT_STATUSES = ['draft', 'published', 'cancelled', 'expired']

RSVP_STATUSES = ['attending', 'maybe', 'not_attending', 'waitlist']


class Event(BaseModel):
    __tablename__ = 'events'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=True, index=True)
    end_date = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    organizer = db.Column(db.String(120), nullable=True)
    capacity = db.Column(db.Integer, default=0)  # 0 means no limit
    status = db.Column(db.String(20), default='draft', index=True)

    rsvps = db.relationship(
        'RSVP',
        backref='event',
        cascade='all, delete-orphan',
        lazy=True,
    )

    def __repr__(self):
        return f'<Event {self.title}>'

    @property
    def attending_count(self):
        return sum(1 for r in self.rsvps if r.status == 'attending')

    @property
    def is_full(self):
        return bool(self.capacity) and self.attending_count >= self.capacity

    def to_dict(self, include_rsvps=False):
        data = super().to_dict()
        data['rsvp_counts'] = {
            'attending': self.attending_count,
            'waitlist': sum(1 for r in self.rsvps if r.status == 'waitlist'),
            'maybe': sum(1 for r in self.rsvps if r.status == 'maybe'),
            'not_attending': sum(1 for r in self.rsvps if r.status == 'not_attending'),
            'total': len(self.rsvps),
        }
        if include_rsvps:
            data['rsvps'] = [r.to_dict() for r in self.rsvps]
        return data


class RSVP(BaseModel):
    __tablename__ = 'event_rsvps'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = db.Column(db.String(36), db.ForeignKey('events.id'), nullable=False, index=True)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=True, index=True)
    # Free-form attendee identifier (e.g. an email or external user id) for
    # attendees who are not tracked CRM contacts.
    user_id = db.Column(db.String(120), nullable=True, index=True)
    status = db.Column(db.String(20), default='attending', index=True)
    notes = db.Column(db.Text, nullable=True)

    contact = db.relationship('Contact', backref='event_rsvps')

    def __repr__(self):
        return f'<RSVP event={self.event_id} user={self.user_id or self.contact_id}>'

    @property
    def attendee_label(self):
        if self.contact:
            return self.contact.full_name()
        return self.user_id or self.id

    def to_dict(self):
        data = super().to_dict()
        data['attendee'] = self.attendee_label
        if self.contact:
            data['contact'] = {'id': self.contact.id, 'full_name': self.contact.full_name()}
        else:
            data['contact'] = None
        return data
