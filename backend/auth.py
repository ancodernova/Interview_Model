from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from prisma import Prisma
import re
import asyncio

bcrypt = Bcrypt()
auth_bp = Blueprint("auth", __name__)
prisma = Prisma()


# ===== REGISTER =====
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validate input
    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"msg": "Username, email, and password are required"}), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", data["email"]):
        return jsonify({"msg": "Invalid email format"}), 400

    async def _register():
        await prisma.connect()

        # Check duplicates
        if await prisma.user.find_unique(where={"email": data["email"]}):
            return jsonify({"msg": "Email already registered"}), 400

        if await prisma.user.find_unique(where={"username": data["username"]}):
            return jsonify({"msg": "Username already taken"}), 400

        # Hash password
        hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

        # Create new user
        await prisma.user.create(
            data={
                "username": data["username"],
                "email": data["email"],
                "passwordHash": hashed_pw,
            }
        )

        await prisma.disconnect()
        return jsonify({"msg": "Registered successfully"}), 201

    return asyncio.run(_register())


# ===== LOGIN =====
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"msg": "Email and password are required"}), 400

    async def _login():
        await prisma.connect()

        user = await prisma.user.find_unique(where={"email": data["email"]})
        await prisma.disconnect()

        if not user or not bcrypt.check_password_hash(user.passwordHash, data["password"]):
            return jsonify({"msg": "Invalid credentials"}), 401

        # JWT identity must be string
        token = create_access_token(identity=str(user.id))

        return jsonify({
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200

    return asyncio.run(_login())
