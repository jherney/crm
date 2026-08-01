import uuid
from models import db, BaseModel

class Contact(BaseModel):
    __tablename__ = 'contacts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(255), nullable=True, unique=True)
    phone = db.Column(db.String(40), nullable=True)
    title = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(40), default='lead')
    tags = db.Column(db.JSON, default=list)
    notes = db.Column(db.Text, nullable=True)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=True)

    company = db.relationship('Company', back_populates='contacts')

    def __repr__(self):
        return f'<Contact {self.first_name} {self.last_name or ""}>'

    def full_name(self):
        return f'{self.first_name} {self.last_name or ""}'.strip()

    def to_dict(self):
        data = super().to_dict()
        data['full_name'] = self.full_name()
        if self.company:
            data['company'] = {'id': self.company.id, 'name': self.company.name}
        else:
            data['company'] = None
        return data
