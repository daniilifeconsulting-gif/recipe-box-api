"""Create and seed recipes.db. Run once after cloning: python init_db.py"""

import sqlite3
import secrets
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    ingredients TEXT NOT NULL,
    instructions TEXT NOT NULL DEFAULT '',
    is_public INTEGER NOT NULL DEFAULT 1,
    owner_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    address TEXT,
    role TEXT NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'admin'))
);
"""

SEED = [
    (
        "Shakshuka",
        "eggs, tomatoes, peppers, onion, cumin, paprika",
        "Simmer the sauce, crack in the eggs, cover until just set.",
        1,
        1,
    ),
    (
        "Overnight oats",
        "rolled oats, milk, yogurt, chia seeds, honey",
        "Stir everything together and refrigerate overnight.",
        1,
        1,
    ),
    (
        "Secret family hot sauce",
        "habaneros, garlic, vinegar, a secret ingredient",
        "If we wrote it down here, it wouldn't be a secret.",
        0,
        1,
    ),
]

connection = sqlite3.connect("recipes.db")
connection.executescript(SCHEMA)

# Safely migrate older databases to support RBAC.
columns = {
    row[1]
    for row in connection.execute("PRAGMA table_info(users)")
}

if "role" not in columns:
    connection.execute(
        "ALTER TABLE users ADD COLUMN role "
        "TEXT NOT NULL DEFAULT 'user' "
        "CHECK (role IN ('user', 'admin'))"
    )
    connection.commit()
    print("Database migrated: role column added.")


# Create a seed owner only if User ID 1 does not exist.
owner = connection.execute(
    "SELECT id FROM users WHERE id = ?",
    (1,)
).fetchone()

if owner is None:
    random_password = secrets.token_urlsafe(48)
    password_hash = generate_password_hash(
        random_password,
        method="pbkdf2:sha256"
    )

    connection.execute(
        """
        INSERT INTO users (id, username, email, password_hash)
        VALUES (?, ?, ?, ?)
        """,
        (1, "seed_recipe_owner", "seed-owner@localhost.invalid", password_hash)
    )
    connection.commit()
existing = connection.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]

if existing == 0:
    owner = connection.execute(
        "SELECT id FROM users WHERE id = ?",
        (1,)
    ).fetchone()

    if owner is None:
        connection.close()
        raise SystemExit(
            "Seed owner User ID 1 does not exist. "
            "Create a test user before seeding recipes."
        )

    connection.executemany(
        "INSERT INTO recipes (title, ingredients, instructions, is_public, owner_id)"
        " VALUES (?, ?, ?, ?, ?)",
        SEED,
    )

    connection.commit()
    print(f"Created recipes.db and seeded {len(SEED)} recipes.")

else:
    print(f"recipes.db already has {existing} recipes - nothing to do.")

connection.close()