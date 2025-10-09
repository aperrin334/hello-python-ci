import pytest
from app import app, db, User, Post, Like, Comment, CommentLike
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Créer un utilisateur test avec un mot de passe en clair
            test_user = User(
                name="Test User",
                username="testuser",
                password="testpassword",  # Mot de passe en clair
                email="test@example.com"
            )
            db.session.add(test_user)
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()


def test_register(client):
    # Test d'inscription réussie
    response = client.post('/register', data={
        'name': 'New User',
        'username': 'newuser',
        'password': 'newpassword',
        'email': 'new@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Vérifie que l'utilisateur est en base
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    # Vérifie le message flash
    with client.session_transaction() as sess:
        flashes = sess.get('_flashes', [])
        assert any('Inscription réussie' in flash[1] for flash in flashes)

def test_login(client):
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'  # Doit correspondre au mot de passe hashé dans la fixture
    }, follow_redirects=True)
    assert response.status_code == 200
    # Vérifie que l'utilisateur est bien en session
    with client.session_transaction() as sess:
        assert 'username' in sess
        assert sess['username'] == 'testuser'


def test_like_post(client):
    # Se connecter
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    # Créer un post
    client.post('/create_post', data={
        'content': 'Post à liker'
    })
    # Récupère le post depuis la base
    post = Post.query.filter_by(content='Post à liker').first()
    assert post is not None
    # Like le post
    response = client.post(f'/like_post/{post.id}', follow_redirects=True)
    assert response.status_code == 200
    # Vérifie que le like est en base
    like = Like.query.filter_by(user_id=1, post_id=post.id).first()
    assert like is not None

def test_create_comment(client):
    # Se connecter
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    # Créer un post
    client.post('/create_post', data={
        'content': 'Post à commenter'
    })
    # Récupère le post
    post = Post.query.filter_by(content='Post à commenter').first()
    assert post is not None
    # Ajoute un commentaire
    response = client.post(f'/comment/{post.id}', data={
        'content': 'Mon premier commentaire !'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Vérifie que le commentaire est en base
    comment = Comment.query.filter_by(content='Mon premier commentaire !').first()
    assert comment is not None

