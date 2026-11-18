from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


def now(): return datetime.now(timezone.utc)

class Organization(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False,unique=True); type=db.Column(db.String(50),default='Campus'); description=db.Column(db.Text); is_active=db.Column(db.Boolean,default=True); created_at=db.Column(db.DateTime(timezone=True),default=now)
class Location(db.Model):
    id=db.Column(db.Integer,primary_key=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id')); name=db.Column(db.String(120),nullable=False,index=True); description=db.Column(db.Text); latitude=db.Column(db.Float); longitude=db.Column(db.Float); is_active=db.Column(db.Boolean,default=True); organization=db.relationship('Organization',backref='locations')
class Category(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(80),nullable=False,unique=True,index=True); description=db.Column(db.Text); is_active=db.Column(db.Boolean,default=True)
class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False); email=db.Column(db.String(255),nullable=False,unique=True,index=True); password_hash=db.Column(db.String(255),nullable=False); role=db.Column(db.String(20),default='USER',index=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id')); phone=db.Column(db.String(30)); is_active_flag=db.Column(db.Boolean,default=True); email_verified=db.Column(db.Boolean,default=False); created_at=db.Column(db.DateTime(timezone=True),default=now); updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now); organization=db.relationship('Organization')
    @property
    def is_active(self): return self.is_active_flag
    def set_password(self,p): self.password_hash=generate_password_hash(p)
    def check_password(self,p): return check_password_hash(self.password_hash,p)
@login_manager.user_loader
def load_user(uid): return db.session.get(User,int(uid))

class Item(db.Model):
    __table_args__=(db.Index('ix_item_type_status','item_type','status'),)
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id')); category_id=db.Column(db.Integer,db.ForeignKey('category.id'),nullable=False,index=True); location_id=db.Column(db.Integer,db.ForeignKey('location.id'),nullable=False,index=True); item_type=db.Column(db.String(10),nullable=False,index=True); title=db.Column(db.String(140),nullable=False,index=True); description=db.Column(db.Text,nullable=False); color=db.Column(db.String(60),index=True); brand=db.Column(db.String(80),index=True); model=db.Column(db.String(80)); date_event=db.Column(db.Date,nullable=False,index=True); time_event=db.Column(db.Time); image_path=db.Column(db.String(255)); image_phash=db.Column(db.String(32)); reported_lat=db.Column(db.Float); reported_lng=db.Column(db.Float); distinguishing_features=db.Column(db.Text); value_level=db.Column(db.String(20),default='NORMAL'); status=db.Column(db.String(30),default='ACTIVE',index=True); visibility=db.Column(db.String(20),default='PUBLIC'); storage_location=db.Column(db.String(160)); created_at=db.Column(db.DateTime(timezone=True),default=now); updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now)
    user=db.relationship('User',backref='items'); organization=db.relationship('Organization'); category=db.relationship('Category'); location=db.relationship('Location')
class PrivateVerificationDetail(db.Model):
    id=db.Column(db.Integer,primary_key=True); item_id=db.Column(db.Integer,db.ForeignKey('item.id'),nullable=False,unique=True); protected_details=db.Column(db.Text,nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=now); updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now); item=db.relationship('Item',backref=db.backref('private_detail',uselist=False,cascade='all, delete-orphan'))
class Match(db.Model):
    __table_args__=(db.UniqueConstraint('lost_item_id','found_item_id',name='uq_match_pair'),)
    id=db.Column(db.Integer,primary_key=True); lost_item_id=db.Column(db.Integer,db.ForeignKey('item.id'),nullable=False,index=True); found_item_id=db.Column(db.Integer,db.ForeignKey('item.id'),nullable=False,index=True); score=db.Column(db.Float,nullable=False,index=True); description_score=db.Column(db.Float); category_score=db.Column(db.Float); location_score=db.Column(db.Float); date_score=db.Column(db.Float); attribute_score=db.Column(db.Float); image_score=db.Column(db.Float); reasons_json=db.Column(db.JSON,default=list); algorithm_version=db.Column(db.String(30),default='tfidf-v1'); status=db.Column(db.String(20),default='POSSIBLE'); created_at=db.Column(db.DateTime(timezone=True),default=now); lost_item=db.relationship('Item',foreign_keys=[lost_item_id]); found_item=db.relationship('Item',foreign_keys=[found_item_id])
class Claim(db.Model):
    __table_args__=(db.UniqueConstraint('item_id','claimant_id','status',name='uq_claim_active'),)
    id=db.Column(db.Integer,primary_key=True); item_id=db.Column(db.Integer,db.ForeignKey('item.id'),nullable=False,index=True); claimant_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True); verification_response_protected=db.Column(db.Text,nullable=False); status=db.Column(db.String(30),default='PENDING',index=True); reviewed_by=db.Column(db.Integer,db.ForeignKey('user.id')); reviewed_at=db.Column(db.DateTime(timezone=True)); review_reason=db.Column(db.Text); created_at=db.Column(db.DateTime(timezone=True),default=now); updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now); item=db.relationship('Item'); claimant=db.relationship('User',foreign_keys=[claimant_id]); reviewer=db.relationship('User',foreign_keys=[reviewed_by])
class Notification(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True); type=db.Column(db.String(40)); title=db.Column(db.String(160)); message=db.Column(db.Text); item_id=db.Column(db.Integer,db.ForeignKey('item.id')); claim_id=db.Column(db.Integer,db.ForeignKey('claim.id')); link=db.Column(db.String(200)); is_read=db.Column(db.Boolean,default=False,index=True); created_at=db.Column(db.DateTime(timezone=True),default=now); user=db.relationship('User',backref='notifications')
Notification.item=db.relationship('Item',foreign_keys=[Notification.item_id])

class AuditLog(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id')); action=db.Column(db.String(80),nullable=False,index=True); entity_type=db.Column(db.String(50)); entity_id=db.Column(db.String(50)); metadata_json=db.Column(db.JSON,default=dict); ip_address=db.Column(db.String(64)); created_at=db.Column(db.DateTime(timezone=True),default=now,index=True); user=db.relationship('User')

class Message(db.Model):
    """Anonymized in-platform chat tied to a claim. Findora relays messages between
    the claimant and the item owner (and admins) without ever revealing email,
    phone number, or account identity — only display aliases (e.g. 'Reporter', 'Claimant')
    are shown. Outgoing text is scanned and personal-contact patterns are masked."""
    id=db.Column(db.Integer,primary_key=True)
    claim_id=db.Column(db.Integer,db.ForeignKey('claim.id'),nullable=False,index=True)
    sender_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    body=db.Column(db.Text,nullable=False)
    was_redacted=db.Column(db.Boolean,default=False)
    created_at=db.Column(db.DateTime(timezone=True),default=now,index=True)
    claim=db.relationship('Claim',backref=db.backref('messages',order_by='Message.created_at',cascade='all, delete-orphan'))
    sender=db.relationship('User')

class Flag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    item_id=db.Column(db.Integer,db.ForeignKey('item.id'),nullable=False,index=True)
    reporter_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    reason=db.Column(db.String(255),nullable=False)
    status=db.Column(db.String(20),default='OPEN',index=True)
    reviewed_by=db.Column(db.Integer,db.ForeignKey('user.id'))
    created_at=db.Column(db.DateTime(timezone=True),default=now)
    item=db.relationship('Item',backref='flags')
    reporter=db.relationship('User',foreign_keys=[reporter_id])
    reviewer=db.relationship('User',foreign_keys=[reviewed_by])


class MatchLog(db.Model):
    """Every lost/found pair the AI engine scored - including pairs that stayed BELOW the threshold.
    Admins use this to justify (or re-examine) why a user's report was or was not matched."""
    __table_args__=(db.UniqueConstraint('lost_item_id','found_item_id',name='uq_matchlog_pair'),)
    id=db.Column(db.Integer,primary_key=True)
    lost_item_id=db.Column(db.Integer,db.ForeignKey('item.id'),nullable=False,index=True)
    found_item_id=db.Column(db.Integer,db.ForeignKey('item.id'),nullable=False,index=True)
    score=db.Column(db.Float,nullable=False,index=True)
    threshold=db.Column(db.Float,nullable=False)
    passed=db.Column(db.Boolean,default=False,index=True)
    description_score=db.Column(db.Float); category_score=db.Column(db.Float); location_score=db.Column(db.Float)
    date_score=db.Column(db.Float); attribute_score=db.Column(db.Float); image_score=db.Column(db.Float)
    reasons_json=db.Column(db.JSON,default=list)
    created_at=db.Column(db.DateTime(timezone=True),default=now)
    updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now)
    lost_item=db.relationship('Item',foreign_keys=[lost_item_id])
    found_item=db.relationship('Item',foreign_keys=[found_item_id])

class Ticket(db.Model):
    """Direct user <-> admin channel: report an issue, hand in a found item, ask why an item was not
    matched, or let an admin contact a user. One thread per ticket."""
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    item_id=db.Column(db.Integer,db.ForeignKey('item.id'))
    kind=db.Column(db.String(30),default='QUESTION')   # QUESTION, DIRECT_REPORT, MATCH_QUERY, ADMIN_CONTACT
    subject=db.Column(db.String(160),nullable=False)
    status=db.Column(db.String(20),default='OPEN',index=True)   # OPEN, ANSWERED, CLOSED
    created_at=db.Column(db.DateTime(timezone=True),default=now)
    updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now)
    user=db.relationship('User',foreign_keys=[user_id],backref='tickets')
    item=db.relationship('Item')
    messages=db.relationship('TicketMessage',backref='ticket',order_by='TicketMessage.created_at',cascade='all, delete-orphan')

class TicketMessage(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    ticket_id=db.Column(db.Integer,db.ForeignKey('ticket.id'),nullable=False,index=True)
    sender_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    from_admin=db.Column(db.Boolean,default=False)
    body=db.Column(db.Text,nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=now)
    sender=db.relationship('User')


class LocationPing(db.Model):
    """Opt-in 'last 6 hours' location trail. Only the user who owns it can read it (never shown to other
    users or admins); rows older than TRAIL_HOURS are deleted automatically."""
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    lat=db.Column(db.Float,nullable=False); lng=db.Column(db.Float,nullable=False)
    accuracy_m=db.Column(db.Float)
    location_id=db.Column(db.Integer,db.ForeignKey('location.id'))   # nearest known campus location at that time
    created_at=db.Column(db.DateTime(timezone=True),default=now,index=True)
    location=db.relationship('Location')

class MatchMessage(db.Model):
    """Anonymized chat between the owner of a LOST report and the finder of a matching FOUND report,
    available as soon as the AI proposes a match (no claim needed). Only role labels are shown."""
    id=db.Column(db.Integer,primary_key=True)
    match_id=db.Column(db.Integer,db.ForeignKey('match.id'),nullable=False,index=True)
    sender_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
    body=db.Column(db.Text,nullable=False)
    was_redacted=db.Column(db.Boolean,default=False)
    created_at=db.Column(db.DateTime(timezone=True),default=now,index=True)
    match=db.relationship('Match',backref=db.backref('messages',order_by='MatchMessage.created_at',cascade='all, delete-orphan'))
    sender=db.relationship('User')
