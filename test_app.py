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
            # Create a test user with a hashed password
            hashed_password = generate_password_hash("testpassword", method='pbkdf2:sha256')
            test_user = User(
                name="Test User",
                username="testuser",
                password=hashed_password,  # Use the hashed password
                email="test@example.com"
            )
            db.session.add(test_user)
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()


def test_register(client):
    # Test successful registration
    response = client.post('/register', data={
        'name': 'New User',
        'username': 'newuser',
        'password': 'newpassword',
        'email': 'new@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check that the user is in the database
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    # Check for the flash message
    # To check flashes, you need to access the session from the response context
    with client.session_transaction() as sess:
        flashes = sess.get('_flashes', [])
        assert any('Inscription réussie' in flash[1] for flash in flashes)

def test_login(client):
    # Test successful login
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'  # Use the plain text password here for the login form
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check that the user is in the session
    with client.session_transaction() as sess:
        assert 'username' in sess # Check for username as user_id might not be in session
        assert sess['username'] == 'testuser'


def test_like_post(client):
    # Log in first to establish a session
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)

    # Create a post by calling the endpoint, like a user would
    client.post('/create_post', data={'content': 'Post to be liked'}, follow_redirects=True)

    # In a separate context, verify the post was created and get its ID
    post_id = None
    user_id = None
    with app.app_context():
        post = Post.query.filter_by(content='Post to be liked').first()
        assert post is not None
        post_id = post.id
        user = User.query.filter_by(username="testuser").first()
        user_id = user.id

    # Like the post using its ID
    response = client.post(f'/like_post/{post_id}', follow_redirects=True)
    assert response.status_code == 200

    # Verify the like is in the database
    with app.app_context():
        like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
        assert like is not None

def test_create_comment(client):
    # Log in first
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    
    # Create a post using the application endpoint
    client.post('/create_post', data={'content': 'Post to be commented on'}, follow_redirects=True)

    # Verify the post was created and get its ID
    post_id = None
    with app.app_context():
        post = Post.query.filter_by(content='Post to be commented on').first()
        assert post is not None
        post_id = post.id

    # Add a comment to the post
    response = client.post(f'/comment/{post_id}', data={
        'content': 'My first comment!'
    }, follow_redirects=True)
    assert response.status_code == 200

    # Verify the comment is in the database
    with app.app_context():
        comment = Comment.query.filter_by(content='My first comment!', post_id=post_id).first()
        assert comment is not None
