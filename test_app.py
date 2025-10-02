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
    assert b'Bienvenue sur notre application' in response.data
    assert b'S&#39;inscrire' in response.data
    assert b'Se connecter' in response.data

def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Inscription' in response.data

def test_register_user(client):
    response = client.post('/register', data={
        'name': 'Test User',
        'username': 'testuser',
        'password': 'testpassword',
        'email': 'test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Bienvenue sur notre application' in response.data

    # Vérifier que l'utilisateur a été ajouté à la base de données
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'

def test_register_existing_user(client):
    # Ajouter un utilisateur existant
    with app.app_context():
        existing_user = User(name='Existing User', username='existinguser', password='password', email='existing@example.com')
        db.session.add(existing_user)
        db.session.commit()

    response = client.post('/register', data={
        'name': 'Test User',
        'username': 'existinguser',
        'password': 'testpassword',
        'email': 'test@example.com'
    })
    assert response.status_code == 200
    assert b'Username déjà existant' in response.data

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Connexion' in response.data

def test_login_user(client):
    # Ajouter un utilisateur pour le test de connexion
    with app.app_context():
        user = User(name='Test User', username='testuser', password='testpassword', email='test@example.com')
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Page de testuser' in response.data

def test_login_invalid_user(client):
    response = client.post('/login', data={
        'username': 'invaliduser',
        'password': 'invalidpassword'
    })
    assert response.status_code == 200
    assert b'Nom d&#39;utilisateur ou mot de passe incorrect' in response.data

def test_profile_page(client):
    # Essayer d'accéder à la page de profil sans être connecté
    response = client.get('/profile', follow_redirects=True)
    assert response.status_code == 200
    assert b'Connexion' in response.data

    # Se connecter et accéder à la page de profil
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'Page de testuser' in response.data
