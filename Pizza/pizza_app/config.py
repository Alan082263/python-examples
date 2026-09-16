import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # In production, set this via an environment variable instead of hardcoding it.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'pizza.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
