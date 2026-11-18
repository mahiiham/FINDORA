from datetime import date
from app.extensions import db
from app.models import User, Item, PrivateVerificationDetail, Claim, Message
from app.utils.file_upload import hamming_distance, image_similarity
from app.utils.ai_helpers import verification_confidence, redact_personal_info
from app.utils.geo import haversine_km
from tests.conftest import login


def test_haversine_km_known_distance():
    # Delhi to Meerut is roughly 60-70km in a straight line
    d = haversine_km(28.6139, 77.2090, 28.9845, 77.7064)
    assert 55 < d < 75
    assert haversine_km(10, 10, 10, 10) == 0.0


def test_hamming_and_image_similarity():
    assert hamming_distance('0f0f0f0f0f0f0f0f', '0f0f0f0f0f0f0f0f') == 0
    assert image_similarity('0000000000000000', '0000000000000000') == 1.0
    assert image_similarity('ffffffffffffffff', '0000000000000000') == 0.0
    assert image_similarity(None, 'abc') is None


def test_verification_confidence_high_and_low():
    high = verification_confidence('The zipper has a small blue thread near the corner', 'small blue thread near the zipper corner')
    low = verification_confidence('It is a red umbrella', 'A silver watch with a scratched face')
    assert high['score'] > low['score']
    assert high['level'] in ('high', 'medium')
    assert low['level'] == 'low'


def test_redact_personal_info_masks_contact_details():
    text, was_redacted = redact_personal_info('Call me at 9876543210 or email me at test@example.com')
    assert was_redacted is True
    assert 'test@example.com' not in text
    assert '9876543210' not in text
    clean_text, clean_flag = redact_personal_info('The bag is near the library entrance')
    assert clean_flag is False
    assert clean_text == 'The bag is near the library entrance'


def _make_claim(app):
    with app.app_context():
        owner = User.query.filter_by(email='other@test.com').first()
        claimant = User.query.filter_by(email='user@test.com').first()
        item = Item(user_id=owner.id, organization_id=1, category_id=1, location_id=1, item_type='FOUND',
                    title='Found wallet', description='Black wallet found near cafeteria', color='Black',
                    date_event=date.today())
        db.session.add(item); db.session.flush()
        db.session.add(PrivateVerificationDetail(item_id=item.id, protected_details='has two cards'))
        claim = Claim(item_id=item.id, claimant_id=claimant.id, verification_response_protected='has two cards inside', status='PENDING')
        db.session.add(claim); db.session.commit()
        return claim.id


def test_map_data_endpoint_requires_login_and_handles_missing_coords(client, app):
    r = client.get('/items/api/map-data')
    assert r.status_code in (302, 401)  # not logged in -> redirected to login
    login(client)
    r = client.get('/items/api/map-data')
    assert r.status_code == 200
    data = r.get_json()
    assert data['window_hours'] == 6
    assert data['locations'] == []  # seeded test Location has no lat/lng
    assert data['nearest_location_id'] is None


def test_messaging_thread_access_control(client, app):
    claim_id = _make_claim(app)
    login(client)  # user@test.com is the claimant
    r = client.get(f'/messages/claim/{claim_id}')
    assert r.status_code == 200
    r = client.post(f'/messages/claim/{claim_id}', data={'body': 'Hi, is this still available?'}, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        assert Message.query.filter_by(claim_id=claim_id).count() == 1

    client.post('/logout')
    # A third, unrelated user must never see the thread
    client.post('/register', data={'name': 'Outsider', 'email': 'outsider@test.com', 'password': 'Pass1234',
                                    'confirm': 'Pass1234', 'organization_id': '1'}, follow_redirects=True)
    r = client.get(f'/messages/claim/{claim_id}')
    assert r.status_code == 403


def test_messaging_redacts_contact_info_in_chat(client, app):
    claim_id = _make_claim(app)
    login(client)
    client.post(f'/messages/claim/{claim_id}', data={'body': 'reach me at 9998887776'}, follow_redirects=True)
    with app.app_context():
        msg = Message.query.filter_by(claim_id=claim_id).first()
        assert msg.was_redacted is True
        assert '9998887776' not in msg.body


# ---------------- v6: dashboards, admin console, AI match log, direct admin contact ----------------
from app.models import MatchLog, Ticket, TicketMessage
from app.matching.service import refresh_matches_for_item
from tests.test_core import _make_items


def test_user_dashboard_and_pages_render(client, app):
    _make_items(app)
    login(client)
    for url in ['/dashboard', '/items', '/claims', '/support', '/notifications']:
        assert client.get(url).status_code == 200, url


def test_ai_logs_every_pair_including_rejected(app):
    with app.app_context():
        u = User.query.filter_by(email='user@test.com').first(); v = User.query.filter_by(email='other@test.com').first()
        lost = Item(user_id=u.id, organization_id=1, category_id=1, location_id=1, item_type='LOST', title='Red umbrella', description='Red folding umbrella', color='Red', date_event=date.today())
        found = Item(user_id=v.id, organization_id=1, category_id=1, location_id=1, item_type='FOUND', title='Silver spoon set', description='Cutlery found in a cafeteria drawer', color='Silver', date_event=date.today())
        db.session.add_all([lost, found]); db.session.commit()
        refresh_matches_for_item(found, 0.99)          # impossible threshold -> must be logged as rejected
        row = MatchLog.query.filter_by(lost_item_id=lost.id, found_item_id=found.id).first()
        assert row is not None and row.passed is False and row.threshold == 0.99 and 0 <= row.score <= 1


def test_admin_console_pages_render(client, app):
    _make_items(app)
    with app.app_context():
        for it in Item.query.all(): refresh_matches_for_item(it, 0.45)
    login(client, 'admin@test.com', 'Admin1234')
    for url in ['/admin', '/admin/items', '/admin/items/1', '/admin/match-log', '/admin/match-log?view=rejected', '/admin/claims', '/admin/tickets', '/admin/users', '/admin/flags', '/admin/audit-logs', '/admin/categories', '/admin/locations', '/admin/organizations']:
        assert client.get(url).status_code == 200, url
    client.post('/logout'); login(client)
    assert client.get('/admin/match-log').status_code == 403   # ordinary users never reach the admin console


def test_direct_admin_contact_both_directions(client, app):
    _make_items(app)
    login(client)
    r = client.post('/support', data={'kind': 'MATCH_QUERY', 'subject': 'Why not matched?', 'item_id': '1', 'body': 'Please check my report.'}, follow_redirects=True)
    assert r.status_code == 200 and b'Why not matched?' in r.data
    with app.app_context():
        t = Ticket.query.first(); tid = t.id
        assert t.status == 'OPEN' and len(t.messages) == 1
    client.post('/logout'); login(client, 'admin@test.com', 'Admin1234')
    assert client.get('/admin/tickets').status_code == 200
    client.post(f'/admin/tickets/{tid}', data={'body': 'Your score was below the threshold.'}, follow_redirects=True)
    with app.app_context():
        t = db.session.get(Ticket, tid); assert t.status == 'ANSWERED' and t.messages[-1].from_admin is True
        uid = User.query.filter_by(email='user@test.com').first().id
    r = client.post(f'/admin/users/{uid}/contact', data={'subject': 'Please visit the desk', 'body': 'Bring your ID card.'}, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context(): assert Ticket.query.filter_by(kind='ADMIN_CONTACT').count() == 1
    client.post('/logout'); login(client)
    assert client.get(f'/support/{tid}').status_code == 200


def test_report_stores_detected_position(client, app):
    login(client)
    r = client.post('/items/create/lost', data={'category_id': 1, 'title': 'Test bag', 'description': 'A test bag lost near the library', 'location_id': 1, 'date_event': date.today().isoformat(), 'value_level': 'NORMAL',
                    'private_details': 'blue thread', 'detected_lat': '29.0160', 'detected_lng': '77.6740'}, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        it = Item.query.filter_by(title='Test bag').first()
        assert it is not None and abs(it.reported_lat - 29.016) < 1e-6 and abs(it.reported_lng - 77.674) < 1e-6


# ---------------- v7: user<->user match chat, location trail, risk suggestions, uploads ----------------
from app.models import Match, MatchMessage, LocationPing, Notification, Location


def _make_match(app):
    ids = _make_items(app)
    with app.app_context():
        for it in Item.query.all(): refresh_matches_for_item(it, 0.30)   # the two sample items are near-identical -> a match is stored
        m = Match.query.first(); assert m is not None
        return m.id


def test_match_chat_between_two_users_is_anonymous_and_protected(client, app):
    mid = _make_match(app)
    login(client)                                                   # user@test.com owns the LOST report
    assert client.get(f'/messages/match/{mid}').status_code == 200
    r = client.post(f'/messages/match/{mid}', data={'body': 'Hi, call me on 9876543210'}, follow_redirects=True)
    assert r.status_code == 200 and b'9876543210' not in r.data and b'Owner (lost item)' in r.data
    with app.app_context():
        msg = MatchMessage.query.filter_by(match_id=mid).first()
        assert msg.was_redacted is True and '9876543210' not in msg.body
        n = Notification.query.filter_by(type='MESSAGE').first()
        assert n is not None and n.link == f'/messages/match/{mid}'    # the other user gets an alert that opens the chat
    client.post('/logout'); login(client, 'other@test.com', 'Test1234')   # the finder sees the reply under a role label
    r = client.get(f'/messages/match/{mid}'); assert r.status_code == 200 and b'Owner (lost item)' in r.data
    assert client.get(f'/messages/match/{mid}/poll').status_code == 200
    client.post('/logout'); client.post('/register', data={'name': 'Outsider', 'email': 'out2@test.com', 'password': 'Pass1234', 'confirm': 'Pass1234', 'organization_id': '1'}, follow_redirects=True)
    assert client.get(f'/messages/match/{mid}').status_code == 403   # nobody else may read it


def test_location_trail_is_private_and_expires(client, app):
    with app.app_context():
        loc = Location.query.first(); loc.latitude = 29.016; loc.longitude = 77.674; db.session.commit()
    login(client)
    r = client.post('/items/api/ping', json={'lat': 29.0161, 'lng': 77.6741, 'accuracy': 20})
    assert r.status_code == 200 and r.get_json()['stored'] is True and r.get_json()['place']
    assert client.post('/items/api/ping', json={'lat': 999, 'lng': 0}).status_code == 400
    stops = client.get('/items/api/trail').get_json()['stops']
    assert len(stops) == 1 and stops[0]['place'] and stops[0]['n'] == 1
    with app.app_context():                                         # old points are purged automatically
        from datetime import timedelta
        from app.models import now
        p = LocationPing.query.first(); p.created_at = now() - timedelta(hours=7); db.session.commit()
    assert client.get('/items/api/trail').get_json()['stops'] == []
    client.post('/items/api/ping', json={'lat': 29.0161, 'lng': 77.6741})
    client.post('/logout'); login(client, 'other@test.com', 'Test1234')
    assert client.get('/items/api/trail').get_json()['stops'] == []      # another user never sees it
    assert client.post('/items/api/trail/clear').status_code == 200


def test_map_data_gives_written_high_risk_suggestions(client, app):
    with app.app_context():
        loc = Location.query.first(); loc.latitude = 29.016; loc.longitude = 77.674
        u = User.query.filter_by(email='user@test.com').first()
        for i in range(3):
            db.session.add(Item(user_id=u.id, organization_id=1, category_id=1, location_id=loc.id, item_type='LOST', title=f'Lost thing {i}', description='x', date_event=date.today()))
        db.session.commit()
    login(client)
    d = client.get('/items/api/map-data?lat=29.0160&lng=77.6740').get_json()
    assert d['nearest']['risk'] == 'high' and 'High-risk' in d['nearest']['tip']
    assert d['suggestions'] and d['suggestions'][0]['lost_count'] == 3 and d['locations'][0]['distance_km'] < 0.05


def test_phone_style_upload_is_stored_upright_and_shown(client, app, tmp_path):
    import io
    app.config['UPLOAD_FOLDER'] = str(tmp_path)   # keep test files out of the real uploads folder
    from PIL import Image
    img = Image.new('RGB', (120, 80), (200, 30, 30)); exif = Image.Exif(); exif[0x0112] = 6   # camera says: rotate 90 degrees
    buf = io.BytesIO(); img.save(buf, 'JPEG', exif=exif); buf.seek(0)
    login(client)
    r = client.post('/items/create/lost', data={'category_id': 1, 'title': 'Photo bag', 'description': 'A bag with a photo attached to the report', 'location_id': 1, 'date_event': date.today().isoformat(),
                    'value_level': 'NORMAL', 'private_details': 'tag details', 'image': (buf, 'IMG_0001.jpg')}, content_type='multipart/form-data', follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        it = Item.query.filter_by(title='Photo bag').first(); assert it and it.image_path and it.image_phash
        name = it.image_path
    assert client.get(f'/items/uploads/{name}').status_code == 200 and client.get(f'/items/uploads/thumb_{name}').status_code == 200
    stored = Image.open(app.config['UPLOAD_FOLDER'] + '/' + name); assert stored.size == (80, 120)   # rotated upright


# ---------------- v8: login, text engine, stickers everywhere ----------------
def test_login_accepts_reserved_looking_demo_email_and_explains_errors(client, app):
    with app.app_context():
        u = User(name='Demo', email='demo@findora.local', role='USER', organization_id=1, email_verified=True); u.set_password('Demo1234'); db.session.add(u); db.session.commit()
    r = client.post('/login', data={'email': 'demo@findora.local', 'password': 'Demo1234'}, follow_redirects=True)
    assert r.status_code == 200 and b'Welcome' in r.data                       # the ".local" address is no longer rejected silently
    client.post('/logout')
    r = client.post('/login', data={'email': 'demo@findora.local', 'password': ''}, follow_redirects=True)
    assert b'Please enter your email and password' in r.data                   # an empty password now gives a visible message
    r = client.post('/login', data={'email': 'demo@findora.local', 'password': 'wrong-password'}, follow_redirects=True)
    assert b'Welcome back' in r.data and b'Welcome,' not in r.data


def test_builtin_text_engine_matches_scikit_learn():
    from app.utils import textsim
    a, b = 'Red backpack with laptop sleeve and blue keychain', 'Red school backpack found near the library with a laptop sleeve'
    assert abs(textsim.builtin_cosine(a, b) - textsim.text_cosine(a, b)) < 1e-9
    assert textsim.builtin_cosine('red bag', 'red bag') > 0.999 and textsim.builtin_cosine('red bag', 'blue umbrella') == 0.0 and textsim.builtin_cosine('', '') == 0.0


def test_reports_without_photo_show_category_sticker_everywhere(client, app):
    ids = _make_items(app)
    login(client)
    assert b'/static/stickers/' in client.get('/items').data                    # search cards
    assert b'/static/stickers/' in client.get('/dashboard').data                # my report dashboard
    assert b'/static/stickers/' in client.get(f'/items/{ids[0]}').data          # detail page
