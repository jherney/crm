import uuid

from models import db, BaseModel


class AutomationRule(BaseModel):
    __tablename__ = 'automation_rules'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    trigger = db.Column(db.String(60), nullable=False, index=True)
    trigger_param = db.Column(db.String(120), nullable=True)
    conditions = db.Column(db.JSON, default=list)
    actions = db.Column(db.JSON, default=list)
    is_enabled = db.Column(db.Boolean, default=True)
    run_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<AutomationRule {self.name}>'

    def to_dict(self):
        data = super().to_dict()
        return data


class AutomationRun(BaseModel):
    __tablename__ = 'automation_runs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = db.Column(db.String(36), db.ForeignKey('automation_rules.id'),
                        nullable=True, index=True)
    rule = db.relationship('AutomationRule', backref='runs')

    event = db.Column(db.String(60), nullable=False, index=True)
    payload = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, index=True)  # success|skipped|error
    message = db.Column(db.String(255), nullable=True)
    ran_at = db.Column(db.DateTime, nullable=False, index=True)

    def __repr__(self):
        return f'<AutomationRun {self.event} {self.status}>'

    def to_dict(self):
        data = super().to_dict()
        # convert DateTime ran_at to iso if not already
        return data
