from app import app
from extensions import db
from models import User

TEST_USERNAME = "testuser"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpass123"

with app.app_context():
    db.create_all()
    existing = User.query.filter_by(username=TEST_USERNAME).first()
    if existing:
        print(f"Test user '{TEST_USERNAME}' already exists — nothing to do.")
    else:
        user = User(username=TEST_USERNAME, email=TEST_EMAIL)
        user.set_password(TEST_PASSWORD)
        db.session.add(user)
        db.session.commit()
        print("Test account created:")
        print(f"  username: {TEST_USERNAME}")
        print(f"  password: {TEST_PASSWORD}")
