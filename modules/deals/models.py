import uuid
from models import db, BaseModel


# Default pipeline stages, in order. Each stage has a probability (used for
# weighted forecast) and a color for the Kanban UI.
DEAL_STAGES = [
    {'key': 'prospect',     'label': 'Prospect',     'probability': 10, 'color': '#7c7cff', 'is_won': False, 'is_lost': False},
    {'key': 'qualified',    'label': 'Qualified',    'probability': 25, 'color': '#5a8dee', 'is_won': False, 'is_lost': False},
    {'key': 'proposal',     'label': 'Proposal',     'probability': 50, 'color': '#f2a93b', 'is_won': False, 'is_lost': False},
    {'key': 'negotiation', 'label': 'Negotiation', 'probability': 75, 'color': '#e96d6d', 'is_won': False, 'is_lost': False},
    {'key': 'closed_won',   'label': 'Closed Won',   'probability': 100, 'color': '#2ecc71', 'is_won': True,  'is_lost': False},
    {'key': 'closed_lost',  'label': 'Closed Lost',  'probability': 0,   'color': '#95a5a6', 'is_won': False, 'is_lost': True},
]


def stage_meta(stage_key):
    """Return stage metadata dict or a sane default for unknown stages."""
    for s in DEAL_STAGES:
        if s['key'] == stage_key:
            return s
    return DEAL_STAGES[0]


class Deal(BaseModel):
    __tablename__ = 'deals'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='USD')
    stage = db.Column(db.String(40), default='prospect', index=True)
    probability = db.Column(db.Integer, default=10)
    expected_close_date = db.Column(db.Date, nullable=True)
    closed_at = db.Column(db.Date, nullable=True)
    source = db.Column(db.String(80), nullable=True)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, default=list)
    owner = db.Column(db.String(120), nullable=True)

    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=True)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=True)

    contact = db.relationship('Contact', backref='deals')
    company = db.relationship('Company', backref='deals')

    def __repr__(self):
        return f'<Deal {self.name} ({self.stage})>'

    def computed_value(self):
        """Weighted value = value * probability / 100."""
        try:
            return round((self.value or 0) * (self.probability or 0) / 100.0, 2)
        except Exception:
            return 0.0

    def to_dict(self):
        data = super().to_dict()
        data['weighted_value'] = self.computed_value()
        if self.contact:
            data['contact'] = {
                'id': self.contact.id,
                'full_name': self.contact.full_name(),
            }
        else:
            data['contact'] = None
        if self.company:
            data['company'] = {
                'id': self.company.id,
                'name': self.company.name,
            }
        else:
            data['company'] = None
        meta = stage_meta(self.stage)
        data['stage_label'] = meta['label']
        data['stage_color'] = meta['color']
        data['is_won'] = meta['is_won']
        data['is_lost'] = meta['is_lost']
        return data
