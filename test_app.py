# test_app.py
import pytest 
from app import app, db, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    with app.app_context():
        db.drop_all()

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to our Twitter-like app!' in response.data

def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

def test_register_user(client):
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'testpassword',
        'email': 'test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome to our Twitter-like app!' in response.data

    # Vérifier que l'utilisateur a été ajouté à la base de données
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'

def test_register_existing_user(client):
    # Ajouter un utilisateur existant
    with app.app_context():
        existing_user = User(username='existinguser', password='password', email='existing@example.com')
        db.session.add(existing_user)
        db.session.commit()

    response = client.post('/register', data={
        'username': 'existinguser',
        'password': 'testpassword',
        'email': 'test@example.com'
    })
    assert response.status_code == 200
    assert b'Username already exists. Please choose a different one.' in response.data

