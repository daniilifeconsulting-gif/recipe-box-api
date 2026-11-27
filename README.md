
# Recipe Box API

A Flask and SQLite REST API developed for the BE104 Security Project.

## Security Features

- User registration with PBKDF2-SHA256 password hashing
- JWT authentication with 30-minute token expiration
- Public and private recipe visibility
- Recipe ownership restrictions
- Protection against unauthorized recipe updates and deletions
- Input validation and parameterized SQL queries

## Requirements

- Python 3.9 or newer
- Flask
- PyJWT

## Installation

Clone the repository, open the project folder, and install dependencies:

```bash
python -m pip install -r requirements.txt
```

Initialize the database:

```bash
python init_db.py
```

This creates the SQLite database, a dedicated seed-owner account, and three sample recipes.

The seed-owner account uses a randomly generated password and is not intended for interactive login.

## Start the API

Set a JWT signing secret:

```bash
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
```

Start the Flask development server:

```bash
python -m flask --app app run --port 5002
```

The API will be available at:

http://127.0.0.1:5002

## Authentication

Register an account using `POST /register`.

Log in using `POST /login` to receive a JWT token.

Include the token when accessing protected endpoints:

```text
Authorization: Bearer YOUR_JWT_TOKEN
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | API information |
| POST | /register | Register a user |
| POST | /login | Authenticate and obtain a JWT |
| GET | /recipes | Retrieve accessible recipes |
| GET | /recipes/&lt;id&gt; | Retrieve an accessible recipe |
| POST | /recipes | Create a recipe |
| PATCH | /recipes/&lt;id&gt; | Update an owned recipe |
| DELETE | /recipes/&lt;id&gt; | Delete an owned recipe |

## Security Test Results

The following tests were performed locally:

| Test | Actual HTTP Response |
|---|---|
| Anonymous recipe update | 401 Unauthorized |
| Owner updates their recipe | 200 OK |
| Non-owner attempts recipe update | 404 Not Found |
| Non-owner attempts recipe deletion | 404 Not Found |

Database verification confirmed that unauthorized update and deletion attempts did not modify or remove the targeted recipe.

Three legacy recipes with missing ownership were migrated to User ID 1. A subsequent ownership integrity check found zero recipes with missing or invalid owners.

## Notes

This project uses Flask's development server for local testing. It is not configured for production deployment.

Never commit JWT secrets, real passwords, or local database files containing user credentials.
