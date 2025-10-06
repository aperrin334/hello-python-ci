from app import app, db, User, Post
 ### lancer ce code permet d'afficher le contenu des bases de données
with app.app_context():
    users = User.query.all()
    posts = Post.query.all()

    print("=== UTILISATEURS ===")
    for u in users:
        print(f"{u.id} | {u.username} | {u.email}")

    print("\n=== POSTS ===")
    for p in posts:
        print(f"{p.id} | {p.author.username} | {p.content} | {p.date_posted}")
