from flask import request
from flask_login import current_user
from app.extensions import db
from app.models import AuditLog


def audit(action, entity_type=None, entity_id=None, metadata=None):
    log = AuditLog(
        user_id=current_user.id if getattr(current_user, 'is_authenticated', False) else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        metadata_json=metadata or {},
        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr)
    )
    db.session.add(log)
