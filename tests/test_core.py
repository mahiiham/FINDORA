from datetime import date
from app.extensions import db
from app.models import User,Item,PrivateVerificationDetail,Claim
from app.matching.service import score_pair
from app.utils.security import protect_text
from tests.conftest import login

def test_login_page_renders_remember_and_submit_fields(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'name="remember"' in response.data
    assert b'name="submit"' in response.data


def test_registration_and_duplicate(client):
    r=client.post('/register',data={'name':'New User','email':'new@test.com','password':'Pass1234','confirm':'Pass1234','organization_id':'1'},follow_redirects=True)
    assert r.status_code==200 and b'Welcome' in r.data
    client.post('/logout',data={})
    r=client.post('/register',data={'name':'New User','email':'new@test.com','password':'Pass1234','confirm':'Pass1234','organization_id':'1'},follow_redirects=True)
    assert b'already exists' in r.data

def test_login_protected_and_admin_auth(client):
    r=client.get('/dashboard'); assert r.status_code in (302,401)
    login(client); assert client.get('/dashboard').status_code==200; assert client.get('/admin').status_code==403
    client.post('/logout'); login(client,'admin@test.com','Admin1234'); assert client.get('/admin').status_code==200

def _make_items(app):
    with app.app_context():
        u=User.query.filter_by(email='user@test.com').first(); v=User.query.filter_by(email='other@test.com').first()
        lost=Item(user_id=u.id,organization_id=1,category_id=1,location_id=1,item_type='LOST',title='Black laptop bag',description='Black HP laptop backpack near library',color='Black',brand='HP',date_event=date.today())
        found=Item(user_id=v.id,organization_id=1,category_id=1,location_id=1,item_type='FOUND',title='Found black HP laptop bag',description='Black HP bag found at library entrance',color='Black',brand='HP',date_event=date.today())
        db.session.add_all([lost,found]); db.session.flush(); db.session.add_all([PrivateVerificationDetail(item_id=lost.id,protected_details=protect_text('blue thread')),PrivateVerificationDetail(item_id=found.id,protected_details=protect_text('blue thread'))]); db.session.commit(); return lost.id,found.id

def test_ai_similarity(app):
    ids=_make_items(app)
    with app.app_context():
        a,b=map(lambda x: db.session.get(Item,x),ids); score,parts,reasons=score_pair(a,b); assert score>0.7; assert 'Same category' in reasons

def test_claim_admin_workflow(client,app):
    lost_id,found_id=_make_items(app)
    login(client)
    r=client.post(f'/claims/item/{found_id}',data={'verification_response':'The bag has a blue thread on the zipper.'},follow_redirects=True); assert b'Claim submitted securely' in r.data
    client.post('/logout'); login(client,'admin@test.com','Admin1234')
    with app.app_context(): cid=Claim.query.first().id
    r=client.post(f'/admin/claims/{cid}/review',data={'reason':'Private detail matches','decision':'approve'},follow_redirects=True); assert b'approved' in r.data.lower()
    with app.app_context(): assert db.session.get(Claim,cid).status=='APPROVED'
