from app import app
from models import User

with app.app_context():
    print("Database file in use:")
    print(" ", app.config["SQLALCHEMY_DATABASE_URI"])
    print()

    users = User.query.all()
    print(f"Users found in that database: {len(users)}")
    for u in users:
        print(f"  - username={u.username!r} email={u.email!r}")
    print()

    u = User.query.filter_by(username="testuser").first()
    if u is None:
        print("No 'testuser' account found in THIS database.")
    else:
        ok = u.check_password("testpass123")
        print(f"Password check for testuser/testpass123: {'PASS' if ok else 'FAIL'}")
