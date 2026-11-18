import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import User,Organization,Location,Category

@pytest.fixture
def app():
    a=create_app(TestingConfig)
    with a.app_context():
        db.create_all()
        org=Organization(name='Test Org'); loc=Location(name='Library',organization=org); cat=Category(name='Bag')
        u=User(name='User',email='user@test.com',role='USER',organization=org); u.set_password('Test1234')
        v=User(name='Other',email='other@test.com',role='USER',organization=org); v.set_password('Test1234')
        admin=User(name='Admin',email='admin@test.com',role='ADMIN',organization=org); admin.set_password('Admin1234')
        db.session.add_all([org,loc,cat,u,v,admin]); db.session.commit()
        yield a
        db.session.remove(); db.drop_all()
@pytest.fixture
def client(app): return app.test_client()

def login(client,email='user@test.com',password='Test1234'):
    return client.post('/login',data={'email':email,'password':password},follow_redirects=True)
