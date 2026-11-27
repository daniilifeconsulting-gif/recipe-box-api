"""Recipe Box API — BE104 Security Project.

Flask and SQLite recipe management API featuring:
- Password-hashed user registration
- JWT authentication with token expiration
- Public and private recipe access
- Owner-restricted recipe creation, updates, and deletion
- Input validation and parameterized SQL queries
"""

import sqlite3
import os
import jwt
from datetime import datetime, timedelta, timezone

from flask import Flask, g, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "recipes.db"

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def recipe_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "ingredients": row["ingredients"],
        "instructions": row["instructions"],
        "is_public": bool(row["is_public"]),
    }

@app.post("/register")
def register():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "valid username required"}), 400

    if not isinstance(email, str) or "@" not in email:
        return jsonify({"error": "valid email required"}), 400

    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        return jsonify({"error": "password must be 12-128 characters"}), 400

    username = username.strip()
    email = email.strip().lower()

    if len(username) > 50 or len(email) > 254:
        return jsonify({"error": "input too long"}), 400

    password_hash = generate_password_hash(
        password, method="pbkdf2:sha256"
    )

    db = get_db()

    try:
        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "username or email already exists"}), 409

    return jsonify({"message": "user registered"}), 201

@app.post("/login")
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "valid username required"}), 400

    if not isinstance(password, str) or not password:
        return jsonify({"error": "valid password required"}), 400

    if len(username) > 50 or len(password) > 128:
        return jsonify({"error": "invalid credentials"}), 400

    secret = app.config.get("JWT_SECRET_KEY")

    if not secret:
        return jsonify({"error": "authentication unavailable"}), 503

    db = get_db()
    user = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username.strip(),)
    ).fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "invalid credentials"}), 401

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": str(user["id"]),
            "username": user["username"],
            "iat": now,
            "exp": now + timedelta(minutes=30)
        },
        secret,
        algorithm="HS256"
    )

    return jsonify({
        "username": user["username"],
        "token": token
    }), 200
def current_user_id():
    auth = request.headers.get("Authorization", "")
    secret = app.config.get("JWT_SECRET_KEY")

    if not secret or not auth.startswith("Bearer "):
        return None

    token = auth[7:].strip()

    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["sub", "iat", "exp"]}
        )

        user_id = int(claims["sub"])

        if user_id <= 0:
            return None

        user = get_db().execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        return user_id if user else None

    except (jwt.InvalidTokenError, ValueError, TypeError):
        return None

@app.get("/")
def hello():
    return jsonify({"message": "Recipe Box API", "recipes": "/recipes"})


@app.get("/recipes")
def list_recipes():
    user_id = current_user_id()

    rows = get_db().execute(
        "SELECT * FROM recipes "
        "WHERE is_public = 1 OR owner_id = ? "
        "ORDER BY id",
        (user_id,)
    ).fetchall()

    return jsonify([recipe_to_dict(r) for r in rows])


@app.get("/recipes/<int:recipe_id>")
def get_recipe(recipe_id):
    user_id = current_user_id()

    row = get_db().execute(
        "SELECT * FROM recipes "
        "WHERE id = ? AND (is_public = 1 OR owner_id = ?)",
        (recipe_id, user_id)
    ).fetchone()

    if row is None:
        return jsonify({"error": "recipe not found"}), 404

    return jsonify(recipe_to_dict(row))

@app.post("/recipes")
def create_recipe():
    user_id = current_user_id()

    if user_id is None:
        return jsonify({"error": "log in first"}), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "a JSON body is required"}), 400

    title = data.get("title")
    ingredients = data.get("ingredients")
    instructions = data.get("instructions", "")
    is_public = data.get("is_public", False)

    for name, value in (
        ("title", title),
        ("ingredients", ingredients),
        ("instructions", instructions)
    ):
        if not isinstance(value, str):
            return jsonify({"error": f"{name} must be text"}), 400

        if name != "instructions" and not value.strip():
            return jsonify({"error": f"{name} cannot be empty"}), 400

        if len(value) > 10000:
            return jsonify({"error": f"{name} is too long"}), 400

    if not isinstance(is_public, bool):
        return jsonify({"error": "is_public must be boolean"}), 400

    if "owner_id" in data:
        return jsonify({"error": "owner_id cannot be supplied"}), 400

    db = get_db()

    try:
        cur = db.execute(
            """INSERT INTO recipes
            (title, ingredients, instructions, is_public, owner_id)
            VALUES (?, ?, ?, ?, ?)""",
            (
                title.strip(),
                ingredients.strip(),
                instructions.strip(),
                int(is_public),
                user_id
            )
        )
        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "a recipe with that title already exists"}), 409

    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (cur.lastrowid,)
    ).fetchone()

    return jsonify(recipe_to_dict(row)), 201

@app.patch("/recipes/<int:recipe_id>")
def update_recipe(recipe_id):
    user_id = current_user_id()

    if user_id is None:
        return jsonify({"error": "log in first"}), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({"error": "a JSON body is required"}), 400

    fields, values = [], []

    for column in ("title", "ingredients", "instructions"):
        if column in data:
            value = data[column]

            if not isinstance(value, str):
                return jsonify({"error": f"{column} must be text"}), 400

            if column != "instructions" and not value.strip():
                return jsonify({"error": f"{column} cannot be empty"}), 400

            if len(value) > 10000:
                return jsonify({"error": f"{column} is too long"}), 400

            fields.append(f"{column} = ?")
            values.append(value.strip())

    if "is_public" in data:
        if not isinstance(data["is_public"], bool):
            return jsonify({"error": "is_public must be boolean"}), 400

        fields.append("is_public = ?")
        values.append(int(data["is_public"]))

    if "owner_id" in data:
        return jsonify({"error": "ownership cannot be changed"}), 400

    if not fields:
        return jsonify({"error": "nothing to update"}), 400

    values.extend([recipe_id, user_id])
    db = get_db()

    try:
        cur = db.execute(
            f"UPDATE recipes SET {', '.join(fields)} WHERE id = ? AND owner_id = ?",
            values
        )
        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "a recipe with that title already exists"}), 409

    if cur.rowcount == 0:
        existing_recipe = db.execute(
            "SELECT owner_id FROM recipes WHERE id = ?",
            (recipe_id,)
        ).fetchone()

        if existing_recipe is None:
            return jsonify({"error": "recipe not found"}), 404

        return jsonify({"error": "forbidden: you do not own this recipe"}), 403

    row = db.execute(
        "SELECT * FROM recipes WHERE id = ? AND owner_id = ?",
        (recipe_id, user_id)
    ).fetchone()

    return jsonify(recipe_to_dict(row)), 200



@app.delete("/recipes/<int:recipe_id>")
def delete_recipe(recipe_id):
    user_id = current_user_id()

    if user_id is None:
        return jsonify({"error": "log in first"}), 401

    db = get_db()

    cur = db.execute(
        "DELETE FROM recipes WHERE id = ? AND owner_id = ?",
        (recipe_id, user_id)
    )

    db.commit()

    if cur.rowcount == 0:
        existing_recipe = db.execute(
            "SELECT owner_id FROM recipes WHERE id = ?",
            (recipe_id,)
        ).fetchone()

        if existing_recipe is None:
            return jsonify({"error": "recipe not found"}), 404

        return jsonify({"error": "forbidden: you do not own this recipe"}), 403

    return "", 204

if __name__ == "__main__":
    app.run(debug=False)
