from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
PARIS = pytz.timezone('Europe/Paris')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'votre_cle_secrete'  # Nécessaire pour utiliser les sessions
db = SQLAlchemy(app)

# ------------------ MODELES ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(PARIS))

#créer les bases de données qui ne le sont pas déjà
with app.app_context():
    db.create_all()

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username déjà existant"

        # Créer un nouvel utilisateur
        new_user = User(name=name, username=username, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()

        flash('Inscription réussie !', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Vérifier si l'utilisateur existe et que le mot de passe est correct
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            flash('Connexion réussie !', 'success')
            return redirect(url_for('profile'))
        else:
            return "Nom d'utilisateur ou mot de passe incorrect."

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.date_posted.desc()).all()
    return render_template('profile.html', user=user, posts=posts)

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'username' not in session:
        flash('Vous devez être connecté pour publier.', 'warning')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    content = request.form['content']
    if not content.strip():
        flash('Le contenu ne peut pas être vide.', 'danger')
        return redirect(url_for('profile'))

    new_post = Post(user_id=user.id, content=content)
    db.session.add(new_post)
    db.session.commit()
    flash('Publication ajoutée !', 'success')

    return redirect(url_for('profile'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))

    query = request.args.get('q', '').strip()
    results = []

    if query:
        # Recherche les utilisateurs dont le nom contient le mot-clé
        results = User.query.filter(User.username.ilike(f'%{query}%')).all()

    return render_template('search_results.html', query=query, results=results)

@app.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.date_posted.desc()).all()
    return render_template('user_profile.html', user=user, posts=posts)

# ------------------ EXECUTION ------------------
if __name__ == '__main__':
    app.run(debug=True)
