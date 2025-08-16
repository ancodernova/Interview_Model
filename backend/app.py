from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from config import Config
from auth import auth_bp
from interview import interview_bp
from flask_cors import CORS
from prisma import Prisma

app = Flask(__name__)
app.config.from_object(Config)

# Setup CORS
CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:3000"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"]
)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Prisma client instance
prisma = Prisma()

@app.before_first_request
def init_prisma():
    """Connect Prisma before first request."""
    import asyncio
    loop = asyncio.get_event_loop()
    if not prisma.is_connected():
        loop.run_until_complete(prisma.connect())

@app.teardown_appcontext
def close_prisma(exception=None):
    """Disconnect Prisma when app shuts down."""
    import asyncio
    loop = asyncio.get_event_loop()
    if prisma.is_connected():
        loop.run_until_complete(prisma.disconnect())

@app.route("/", methods=["GET"])
def cron_test():
    return "HI", 200

# Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(interview_bp, url_prefix="/api/interview")

if __name__ == "__main__":
    app.run(debug=True)
