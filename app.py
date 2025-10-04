from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash,generate_password_hash # Pour vérifier le hash du mot de passe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'votre_cle_secrete'  # Nécessaire pour utiliser les sessions
db = SQLAlchemy(app)

# Modèle pour la table User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Créer la base de données
with app.app_context():
    db.create_all()

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
        user = User.query.filter_by(username=username).first()
        
        #Vérifie le nom d'utilisateur n'existe pas 
        if not user:
            flash( "Nom d'utilisateur n'existe pas.",'error')
            return redirect(url_for('login'))
        #Sachant que le username est le bon, on vérifie le mot de passe   
        elif  user.username==username  and user.password==password:       #check_password_hash(user.password, password) :
            session['username'] = username
            flash('Connexion réussie !', 'success')
            return redirect(url_for('profile'))
        else :
            flash('Mot de passe incorrect', 'error')
            return redirect(url_for('login'))

    
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        return f"Page de {username}"
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)
