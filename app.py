from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import check_password_hash,generate_password_hash # Pour vérifier le hash du mot de passe

from datetime import datetime
import pytz
PARIS = pytz.timezone('Europe/Paris')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'votre_cle_secrete'  # Nécessaire pour utiliser les sessions
db = SQLAlchemy(app)

# ------------------ MODELES ------------------
############follows
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
)


#############
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    biography = db.Column(db.Text, nullable=True)  
    posts = db.relationship('Post', backref='author', lazy=True)
    
    followed = db.relationship(
        'User',
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    # ------------------- Méthodes pour suivre / unfollow / vérifier -------------------
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.followed.count()


#######POSTS ET LIKES
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(PARIS))
    likes = db.relationship('Like', backref='post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    date_liked = db.Column(db.DateTime, default=lambda: datetime.now(PARIS))

    # Un utilisateur ne peut liker un post qu'une seule fois
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_like'),)
##########



#######COMMENTAIRES
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(PARIS))
    
    # Relation vers l'auteur
    author = db.relationship('User', backref='comments', lazy=True)
    
    likes = db.relationship('CommentLike', backref='comment', lazy=True)

class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_liked = db.Column(db.DateTime, default=lambda: datetime.now(PARIS))
##############




#créer les bases de données qui ne le sont pas déjà
with app.app_context():
    db.create_all()

# ------------------ ROUTES ------------------
#########AUTHENTIFICATION ET PROFIL
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
        new_user = User(name=name, username=username, password=generate_password_hash(password), email=email)
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
        elif  user.username==username  and check_password_hash(user.password,password):   
            session['username'] = username
            #flash('Connexion réussie !', 'success')
            return redirect(url_for('profile'))
        else :
            flash('Mot de passe incorrect', 'error')
            return redirect(url_for('login'))

    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    current_user = User.query.filter_by(username=session['username']).first()
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.date_posted.desc()).all()
    # Liste des posts likés
    liked_post_ids = [like.post_id for like in Like.query.filter_by(user_id=current_user.id).all()]
    # Liste des commentaires likés
    liked_comment_ids = [like.comment_id for like in CommentLike.query.filter_by(user_id=current_user.id).all()]
    return render_template(
        'profile.html',
        user=current_user,
        posts=posts,
        current_user=current_user,
        liked_post_ids=liked_post_ids,
        liked_comment_ids=liked_comment_ids
    )
#########################


############POSTS COMMENTAIRES ET LIKES
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

@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    post = Post.query.get_or_404(post_id)
    # Vérifier si l'utilisateur a déjà liké ce post
    existing_like = Like.query.filter_by(user_id=user.id, post_id=post.id).first()
    if existing_like:
        # Si déjà liké, on supprime le like
        db.session.delete(existing_like)
    else:
        # Sinon, on ajoute un like
        new_like = Like(user_id=user.id, post_id=post.id)
        db.session.add(new_like)
    db.session.commit()
    return redirect(request.referrer or url_for('profile'))
    # Redirige vers la page précédente
    return redirect(request.referrer or url_for('profile'))


@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get(post_id)
    # Supprimer les likes et commentaires liés au post (optionnel)
    Like.query.filter_by(post_id=post_id).delete()
    Comment.query.filter_by(post_id=post_id).delete()
        # Supprimer les likes et commentaires liés au post (optionnel)
    Like.query.filter_by(post_id=post_id).delete()
    Comment.query.filter_by(post_id=post_id).delete()
    # Supprimer le post
    db.session.delete(post)
    db.session.commit()
    flash('Votre post a été supprimé avec succès.', 'success')
    return redirect(url_for('profile'))


@app.route('/comment/<int:post_id>', methods=['POST'])
def create_comment(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    post = Post.query.get_or_404(post_id)
    content = request.form['content'].strip()
    if not content:
        flash('Le commentaire ne peut pas être vide.', 'warning')
        return redirect(request.referrer or url_for('profile'))
    comment = Comment(post_id=post.id, user_id=user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    return redirect(request.referrer or url_for('profile'))

@app.route('/like_comment/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    comment = Comment.query.get_or_404(comment_id)
    existing_like = CommentLike.query.filter_by(user_id=user.id, comment_id=comment.id).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = CommentLike(user_id=user.id, comment_id=comment.id)
        db.session.add(new_like)
    db.session.commit()
    return redirect(request.referrer or url_for('profile'))
##################

##########FOLLOWS/UNFOLLOWS
@app.route('/follow/<int:user_id>', methods=['POST'])
def follow_user(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    current_user = User.query.filter_by(username=session['username']).first()
    user_to_follow = User.query.get_or_404(user_id)

    if current_user.id == user_to_follow.id:
        flash("Vous ne pouvez pas vous suivre vous-même.", "error")
        return redirect(request.referrer)

    current_user.follow(user_to_follow)
    db.session.commit()
    return redirect(request.referrer or url_for('profile'))

@app.route('/unfollow/<int:user_id>', methods=['POST'])
def unfollow_user(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    current_user = User.query.filter_by(username=session['username']).first()
    user_to_unfollow = User.query.get_or_404(user_id)

    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    return redirect(request.referrer or url_for('profile'))

##################




###########RECHERCHE ET AUTRE PROFILES D UTILISATEURS
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '').strip()
    results = []
    if query:
        # Recherche les utilisateurs dont le nom contient le mot-clé (insensible à la casse)
        results = User.query.filter(User.name.ilike(f'%{query}%')).all()
    return render_template('search_results.html', query=query, results=results)

@app.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.date_posted.desc()).all()
    current_user = None
    liked_post_ids = []
    liked_comment_ids = []
    if 'username' in session:
        current_user = User.query.filter_by(username=session['username']).first()
        liked_post_ids = [like.post_id for like in Like.query.filter_by(user_id=current_user.id).all()]
        liked_comment_ids = [like.comment_id for like in CommentLike.query.filter_by(user_id=current_user.id).all()]
    return render_template(
        'user_profile.html',
        user=user,
        posts=posts,
        current_user=current_user,
        liked_post_ids=liked_post_ids,
        liked_comment_ids=liked_comment_ids
    )
@app.route('/edit_biography', methods=['GET', 'POST'])
def edit_biography():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        user.biography = request.form.get('biography', '')
        db.session.commit()
        flash('Biographie mise à jour avec succès !', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_biography.html', user=user)

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    user = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        # Supprimer tous les likes de l'utilisateur
        Like.query.filter_by(user_id=user.id).delete()
        CommentLike.query.filter_by(user_id=user.id).delete()

        # Supprimer tous les commentaires de l'utilisateur
        Comment.query.filter_by(user_id=user.id).delete()

        # Supprimer tous les posts de l'utilisateur
        Post.query.filter_by(user_id=user.id).delete()

        # Supprimer l'utilisateur
        db.session.delete(user)
        db.session.commit()

        # Déconnecter l'utilisateur
        session.pop('username', None)
        flash('Votre compte a été supprimé avec succès.', 'success')
        return redirect(url_for('home'))

    return render_template('delete_account.html', user=user)




# ------------------ EXECUTION ------------------

if __name__ == '__main__':
    app.run(debug=True)
