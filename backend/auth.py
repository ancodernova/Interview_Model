from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from models import db, User
import re

bcrypt = Bcrypt()
auth_bp = Blueprint("auth", __name__)

# ===== REGISTER =====
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validate input
    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"msg": "Username, email, and password are required"}), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", data["email"]):
        return jsonify({"msg": "Invalid email format"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"msg": "Email already registered"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "Username already taken"}), 400

    # Hash password
    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    new_user = User(
        username=data["username"],
        email=data["email"],
        password_hash=hashed_pw
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "Registered successfully"}), 201


# ===== LOGIN =====
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"msg": "Email and password are required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data["password"]):
        return jsonify({"msg": "Invalid credentials"}), 401

    # FIX: JWT identity must be a string
    token = create_access_token(identity=str(user.id))

    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200
