from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

class BaseModel(db.Model, TimestampMixin):
    __abstract__ = True

    def to_dict(self):
        data = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat() if val else None
            data[col.name] = val
        return data

    @classmethod
    def default_columns(cls):
        return [c.name for c in cls.__table__.columns]
