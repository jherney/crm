import uuid
from models import db, BaseModel

class Company(BaseModel):
    __tablename__ = 'companies'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    address = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(40), default='prospect')  # prospect, customer, partner, vendor, competitor
    tags = db.Column(db.JSON, default=list)
    notes = db.Column(db.Text, nullable=True)

    contacts = db.relationship('Contact', back_populates='company')

    def __repr__(self):
        return f'<Company {self.name}>'

    def to_dict(self):
        data = super().to_dict()
        data['contact_count'] = len(self.contacts)
        return data
