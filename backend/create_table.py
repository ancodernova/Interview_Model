import os
from flask import Flask
from models import db

app = Flask(__name__)

# SQLite database in backend folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "interview.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

if __name__ == "__main__":
    with app.app_context():
        # Drop existing DB by deleting file
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"🗑 Deleted existing database at {DB_PATH}")

        db.create_all()
        print(f"✅ Fresh database created at {DB_PATH}")
