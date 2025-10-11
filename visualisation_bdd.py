from app import app, db, User, Post, Like,Comment,CommentLike
import os

if os.path.exists("users.db"):
    os.remove("users.db")

with app.app_context():
    db.create_all()
    print("Base de données recréée ✅")

# On exécute les actions à l'intérieur du contexte de l'app Flask
with app.app_context():
    User.query.delete()
    Post.query.delete()
    Like.query.delete()
    Comment.query.delete()
    CommentLike.query.delete()
    db.session.commit()
    print("Base de données vidée ✅")

with app.app_context():
    db.create_all()
    
with app.app_context():
    users = User.query.all()
    posts = Post.query.all()
    comm=Comment.query.all()
    print("=== UTILISATEURS ===")
    for u in users:
        print(f"{u.id} | {u.username} | {u.email}| {u.password}")

    print("=== Commentaires ===")
    for u in comm:
        print(f"{u.id} | {u.author.username} | {u.post.id}| {u.content}| {u.date_posted} | {u.likes}")

    print("\n=== POSTS ===")
    for p in posts:
        print(f"{p.id} | {p.author.username} | {p.content} | {p.date_posted}")
