import pytest
from flask import template_rendered, session
from flask_testing import TestCase
from app import app, db, User, Post, Like, Comment, CommentLike
from werkzeug.security import generate_password_hash

# Configuration pour les tests
class BaseTestCase(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    def setUp(self):
        db.create_all()
        # Créer un utilisateur test
        hashed_password = generate_password_hash("testpassword")
        test_user = User(name="Test User", username="testuser", password=hashed_password, email="test@example.com")
        db.session.add(test_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

# Test d'inscription
def test_register(client):
    response = client.post('/register', data={
        'name': 'New User',
        'username': 'newuser',
        'password': 'newpassword',
        'email': 'new@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Inscription r&#233;ussie' in response.data
    user = User.query.filter_by(username='newuser').first()
    assert user is not None

# Test de connexion
def test_login(client):
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Connexion r&#233;ussie' in response.data
    with client.session_transaction() as sess:
        assert sess['username'] == 'testuser'

# Test de création de post
def test_create_post(client):
    # Se connecter d'abord
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    # Créer un post
    response = client.post('/create_post', data={
        'content': 'Mon premier post !'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Publication ajout&#233;e' in response.data
    post = Post.query.filter_by(content='Mon premier post !').first()
    assert post is not None

# Test de recherche d'utilisateur
def test_search(client):
    response = client.get('/search?q=Test', follow_redirects=True)
    assert response.status_code == 200
    assert b'Test User' in response.data

# Test de like/unlike d'un post
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
    post = Post.query.filter_by(content='Post à liker').first()
    # Liker le post
    response = client.post(f'/like_post/{post.id}', follow_redirects=True)
    assert response.status_code == 200
    like = Like.query.filter_by(user_id=1, post_id=post.id).first()
    assert like is not None
    # Unlike le post
    response = client.post(f'/like_post/{post.id}', follow_redirects=True)
    like = Like.query.filter_by(user_id=1, post_id=post.id).first()
    assert like is None

# Test de commentaire
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
    post = Post.query.filter_by(content='Post à commenter').first()
    # Ajouter un commentaire
    response = client.post(f'/comment/{post.id}', data={
        'content': 'Mon premier commentaire !'
    }, follow_redirects=True)
    assert response.status_code == 200
    comment = Comment.query.filter_by(content='Mon premier commentaire !').first()
    assert comment is not None

# Test de like/unlike d'un commentaire
def test_like_comment(client):
    # Se connecter
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    # Créer un post et un commentaire
    client.post('/create_post', data={'content': 'Post avec commentaire'})
    post = Post.query.filter_by(content='Post avec commentaire').first()
    client.post(f'/comment/{post.id}', data={'content': 'Commentaire à liker'})
    comment = Comment.query.filter_by(content='Commentaire à liker').first()
    # Liker le commentaire
    response = client.post(f'/like_comment/{comment.id}', follow_redirects=True)
    assert response.status_code == 200
    like = CommentLike.query.filter_by(user_id=1, comment_id=comment.id).first()
    assert like is not None
    # Unlike le commentaire
    response = client.post(f'/like_comment/{comment.id}', follow_redirects=True)
    like = CommentLike.query.filter_by(user_id=1, comment_id=comment.id).first()
    assert like is None
