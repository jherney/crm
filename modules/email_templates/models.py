import uuid
import re

from models import db, BaseModel


# Available merge fields — exposed in the UI for the user.
MERGE_FIELDS = [
    'contact.first_name', 'contact.last_name', 'contact.full_name',
    'contact.email', 'contact.title',
    'company.name', 'company.industry',
    'deal.name', 'deal.value', 'deal.stage',
    'user.name', 'user.email',
]


class EmailTemplate(BaseModel):
    __tablename__ = 'email_templates'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), default='general')
    is_active = db.Column(db.Boolean, default=True)
    use_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

    @staticmethod
    def merge_fields(body, context):
        """Replace {{field.path}} placeholders with values from context dict."""
        def replace(m):
            path = m.group(1).strip()
            cur = context
            for part in path.split('.'):
                if cur is None:
                    return ''
                if hasattr(cur, part):
                    cur = getattr(cur, part)
                elif isinstance(cur, dict):
                    cur = cur.get(part)
                else:
                    return ''
            return '' if cur is None else str(cur)
        return re.sub(r'\{\{\s*([\w.]+)\s*\}\}', replace, body or '')

    def render(self, context):
        return {
            'subject': self.merge_fields(self.subject, context),
            'body': self.merge_fields(self.body, context),
        }

    def to_dict(self):
        data = super().to_dict()
        return data
