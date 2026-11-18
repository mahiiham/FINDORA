"""Load clean sample data for the MIET demo: `python seed.py`
Rebuilds the database (drops everything first), copies the sample photos into uploads/ and runs the
real AI matching engine on the sample reports, so scores, matches and rejected pairs are genuine."""
import shutil
from datetime import timedelta, time
from pathlib import Path
from PIL import Image
from app import create_app
from app.extensions import db
from app.models import (Organization, Location, Category, User, Item, PrivateVerificationDetail, Match, MatchLog, MatchMessage, LocationPing, Claim, Message,
                        Notification, AuditLog, Flag, Ticket, TicketMessage, now)
from app.matching.service import refresh_matches_for_item
from app.utils.security import protect_text
from app.utils.file_upload import compute_phash
import sample_data as SD

app = create_app()
BASE = Path(__file__).resolve().parent
SAMPLE = BASE / 'app' / 'static' / 'sample'

with app.app_context():
    db.drop_all(); db.create_all()
    uploads = Path(app.config['UPLOAD_FOLDER']); uploads.mkdir(parents=True, exist_ok=True)
    threshold = app.config['MATCH_THRESHOLD']

    org = Organization(name=SD.ORG, type='College'); db.session.add(org); db.session.flush()
    clat, clng = SD.CAMPUS_CENTER
    locs = {}
    for name, dlat, dlng in SD.LOCATIONS:
        l = Location(organization_id=org.id, name=name, latitude=round(clat + dlat, 6), longitude=round(clng + dlng, 6)); db.session.add(l); locs[name] = l
    cats = {}
    for name in SD.CATEGORIES:
        c = Category(name=name, description=f'{name} items'); db.session.add(c); cats[name] = c

    admin = User(name=SD.ADMIN[0], email=SD.ADMIN[1], role='ADMIN', organization_id=org.id, email_verified=True, phone='9000000000'); admin.set_password(SD.ADMIN[2]); db.session.add(admin)
    users = []
    for name, email, phone in SD.USERS:
        u = User(name=name, email=email, role='USER', organization_id=org.id, email_verified=True, phone=phone); u.set_password(SD.USER_PASSWORD); db.session.add(u); users.append(u)
    db.session.commit()

    # ---------- reports (with photos, private proofs and GPS) ----------
    t0 = now(); items = {}
    for idx, d in enumerate(SD.ITEMS):
        created = t0 - timedelta(days=d['days'], hours=d.get('hours', 0), minutes=idx * 7)
        photo = None; phash = None
        if d['photo']:
            photo = f"sample_{d['photo']}.jpg"
            shutil.copy(SAMPLE / f"{d['photo']}.jpg", uploads / photo); shutil.copy(SAMPLE / f"thumb_{d['photo']}.jpg", uploads / f'thumb_{photo}')
            phash = compute_phash(Image.open(SAMPLE / f"{d['photo']}.jpg"))
        loc = locs[d['loc']]
        lat = lng = None
        if d['gps']:
            lat = round(loc.latitude + ((idx % 5) - 2) * 0.00011, 6); lng = round(loc.longitude + ((idx % 3) - 1) * 0.00013, 6)
        it = Item(user_id=users[d['owner']].id, organization_id=org.id, category_id=cats[d['cat']].id, location_id=loc.id, item_type=d['type'], title=d['title'], description=d['desc'],
                  color=d['color'] or None, brand=d['brand'] or None, model=d['model'] or None, date_event=created.date(), time_event=time(9 + idx % 8, (idx * 11) % 60),
                  image_path=photo, image_phash=phash, reported_lat=lat, reported_lng=lng, distinguishing_features=d['feat'] or None,
                  value_level='HIGH' if d['cat'] in ('Laptop', 'Mobile Phone') else 'NORMAL', storage_location='Admin Block lost & found desk' if d['type'] == 'FOUND' and idx % 2 else None,
                  created_at=created, updated_at=created)
        db.session.add(it); db.session.flush()
        db.session.add(PrivateVerificationDetail(item_id=it.id, protected_details=protect_text(d['private'])))
        db.session.add(AuditLog(user_id=it.user_id, action='REPORT_CREATED', entity_type='Item', entity_id=str(it.id), metadata_json={'type': d['type']}, ip_address='127.0.0.1', created_at=created))
        db.session.commit()
        items[d['key']] = it
        refresh_matches_for_item(it, threshold)   # real AI scoring: stores matches AND every below-threshold pair

    # ---------- claims, chats, decisions ----------
    claims = {}
    for i, cd in enumerate(SD.CLAIMS):
        item = items[cd['item']]; filed = t0 - timedelta(hours=20 - i * 3)
        c = Claim(item_id=item.id, claimant_id=users[cd['claimant']].id, verification_response_protected=protect_text(cd['answer']), status='PENDING', created_at=filed)
        db.session.add(c); db.session.flush(); claims[cd['key']] = c
        db.session.add(Notification(user_id=item.user_id, type='CLAIM', title='New claim on your report', message=f'Someone claimed "{item.title}". The admin will verify it.', item_id=item.id, claim_id=c.id))
        item.status = 'CLAIM_PENDING'
        if cd['status'] in ('APPROVED', 'REJECTED'):
            c.status = cd['status']; c.reviewed_by = admin.id; c.reviewed_at = filed + timedelta(hours=2); c.review_reason = cd['note']
            item.status = 'CLAIM_APPROVED' if cd['status'] == 'APPROVED' else 'ACTIVE'
            word = cd['status'].lower()
            db.session.add(Notification(user_id=c.claimant_id, type='CLAIM_DECISION', title=f'Claim {word}', message=f'Your claim for "{item.title}" was {word}.', item_id=item.id, claim_id=c.id))
            db.session.add(AuditLog(user_id=admin.id, action=f'CLAIM_{cd["status"]}', entity_type='Claim', entity_id=str(c.id), ip_address='127.0.0.1', created_at=c.reviewed_at))
    for key in SD.RETURNED_ITEMS: items[key].status = 'RETURNED'
    for ckey, msgs in SD.CHATS.items():
        c = claims[ckey]; reporter_id = c.item.user_id
        for j, (who, text, redacted) in enumerate(msgs):
            db.session.add(Message(claim_id=c.id, sender_id=c.claimant_id if who == 'claimant' else reporter_id, body=text, was_redacted=redacted, created_at=t0 - timedelta(hours=10, minutes=-j * 6)))
        db.session.add(Notification(user_id=reporter_id, type='MESSAGE', title='New message', message='You have a new anonymized message about a claim.', item_id=c.item_id, claim_id=c.id))
    db.session.add(Flag(item_id=items['hood_f'].id, reporter_id=users[0].id, reason='Looks like a duplicate of another sweatshirt report', status='OPEN'))

    # ---------- direct user <-> admin messages ----------
    log = MatchLog.query.filter_by(lost_item_id=items['pouch_l'].id, found_item_id=items['purse_f'].id).first()
    t1 = Ticket(user_id=users[2].id, item_id=items['pouch_l'].id, kind='MATCH_QUERY', subject='Why was my wallet not matched?', status='ANSWERED', created_at=t0 - timedelta(hours=8), updated_at=t0 - timedelta(hours=6))
    t2 = Ticket(user_id=users[4].id, item_id=items['watch_f'].id, kind='DIRECT_REPORT', subject='I handed a found watch to the admin desk', status='OPEN', created_at=t0 - timedelta(hours=1), updated_at=t0 - timedelta(hours=1))
    t3 = Ticket(user_id=users[0].id, item_id=items['keys_f'].id, kind='ADMIN_CONTACT', subject='Collect your keys from the Admin Block', status='OPEN', created_at=t0 - timedelta(hours=5), updated_at=t0 - timedelta(hours=2))
    db.session.add_all([t1, t2, t3]); db.session.flush()
    db.session.add_all([
        TicketMessage(ticket_id=t1.id, sender_id=users[2].id, from_admin=False, body='I reported my yellow pouch wallet two days ago and nothing matched. Is the system working?', created_at=t0 - timedelta(hours=8)),
        TicketMessage(ticket_id=t1.id, sender_id=admin.id, from_admin=True, created_at=t0 - timedelta(hours=6),
                      body=f'Yes, it is working. Your pouch was compared with the pink coin purse found at the cafeteria and scored {round(log.score * 100)}%, below the {round(threshold * 100)}% threshold, because the colour and description differ. Your report stays active and is compared with every new found report.'),
        TicketMessage(ticket_id=t2.id, sender_id=users[4].id, from_admin=False, body='I found a brown strap watch and left it at the Admin Block desk. Please add it to the system.', created_at=t0 - timedelta(hours=1)),
        TicketMessage(ticket_id=t3.id, sender_id=admin.id, from_admin=True, body='Your claim for the keys was approved. Please bring your MIET ID card to the Admin Block desk to collect them.', created_at=t0 - timedelta(hours=5)),
        TicketMessage(ticket_id=t3.id, sender_id=users[0].id, from_admin=False, body='Thank you, I will come at 2 pm today.', created_at=t0 - timedelta(hours=2)),
    ])
    # ---------- anonymized user <-> user chats on AI matches ----------
    for _name, (lk, fk, msgs) in SD.MATCH_CHATS.items():
        m = Match.query.filter_by(lost_item_id=items[lk].id, found_item_id=items[fk].id).first()
        if m is None: continue
        for j, (who, text, redacted) in enumerate(msgs):
            sender = items[lk].user_id if who == 'owner' else items[fk].user_id
            db.session.add(MatchMessage(match_id=m.id, sender_id=sender, body=text, was_redacted=redacted, created_at=t0 - timedelta(hours=2, minutes=-j * 5)))
        for uid in (items[lk].user_id, items[fk].user_id):
            db.session.add(Notification(user_id=uid, type='MESSAGE', title='New message about a possible match', message='Someone replied in an anonymized chat about your report.', item_id=items[lk].id if uid == items[lk].user_id else items[fk].id, link=f'/messages/match/{m.id}'))

    # ---------- opt-in 6-hour location trail (sample for user1) ----------
    for hrs, place in SD.TRAIL:
        loc = locs[place]
        db.session.add(LocationPing(user_id=users[0].id, lat=round(loc.latitude + 0.00005, 6), lng=round(loc.longitude - 0.00005, 6), accuracy_m=18, location_id=loc.id, created_at=t0 - timedelta(hours=hrs)))

    db.session.add(Notification(user_id=users[2].id, type='SUPPORT', title='The admin replied', message='Ticket: Why was my wallet not matched?'))
    db.session.add(Notification(user_id=admin.id, type='SUPPORT', title='New message from a user', message='Ticket: I handed a found watch to the admin desk'))
    db.session.add(AuditLog(user_id=admin.id, action='TICKET_REPLIED', entity_type='Ticket', entity_id=str(t1.id), ip_address='127.0.0.1', created_at=t0 - timedelta(hours=6)))
    db.session.commit()

    print('Sample data loaded for', SD.ORG)
    print(f'  {len(users)} users + 1 admin, {MatchMessage.query.count()} match-chat messages, {LocationPing.query.count()} trail points, {len(SD.ITEMS)} reports, {len(SD.CLAIMS)} claims, {Message.query.count()} chat messages, {Ticket.query.count()} admin messages')
    print(f'  AI: threshold {round(threshold * 100)}%, {MatchLog.query.filter_by(passed=True).count()} pairs matched, {MatchLog.query.filter_by(passed=False).count()} rejected by threshold')
    print('Logins:  user1@findora-demo.com ... user5@findora-demo.com / Demo1234   |   admin@findora-demo.com / Admin1234')
