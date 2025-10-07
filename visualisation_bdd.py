from app import app, db, User, Post, Like

# On exécute les actions à l'intérieur du contexte de l'app Flask
""" with app.app_context():
    User.query.delete()
    Post.query.delete()
    Like.query.delete()
    db.session.commit()
    print("Base de données vidée ✅")
 """
with app.app_context():
    users = User.query.all()
    posts = Post.query.all()

    print("=== UTILISATEURS ===")
    for u in users:
        print(f"{u.id} | {u.username} | {u.email}| {u.password}")

    print("\n=== POSTS ===")
    for p in posts:
        print(f"{p.id} | {p.author.username} | {p.content} | {p.date_posted}")
