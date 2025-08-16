from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from models import db
from config import Config
from auth import auth_bp
from interview import interview_bp
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)

CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:3000"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"]
)


db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

@app.route("/", methods=["GET"])
def cron_Test():
    return "HI",200 

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(interview_bp, url_prefix="/api/interview")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
