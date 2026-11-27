
# Recipe Box API

A Flask and SQLite REST API developed for the BE104 Security Project.

## Security Features

- User registration with PBKDF2-SHA256 password hashing
- JWT authentication with 30-minute token expiration
- Public and private recipe visibility
- Role-based access control (RBAC) with admin and user roles
- Recipe ownership restrictions with administrator override
- Protection against registration privilege escalation
- Database role verification for authorization
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

Database initialization also migrates older users tables that lack a role column. Existing role assignments are preserved, and newly assigned roles default to user.

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

Log in using `POST /login` to receive a JWT token containing the user ID, username, role, issued-at time, and expiration.

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
| PATCH | /recipes/&lt;id&gt; | Update a recipe as its owner or an administrator |
| DELETE | /recipes/&lt;id&gt; | Delete a recipe as its owner or an administrator |

## Role-Based Access Control

| Permission | Anonymous | User | Admin |
|---|---|---|---|
| Read public recipes | Yes | Yes | Yes |
| Read own private recipes | No | Yes | Yes |
| Read other users' private recipes | No | No | Yes |
| Create recipes | No | Yes | Yes |
| Update own recipes | No | Yes | Yes |
| Update other users' recipes | No | No | Yes |
| Delete own recipes | No | Yes | Yes |
| Delete other users' recipes | No | No | Yes |
| List all recipes | No | No | Yes |

New accounts receive the user role by default.
Registration cannot assign administrator privileges.

Administrator roles must be assigned through a trusted
database administration operation.

JWT signatures and expiration are validated before
protected operations. Administrator authorization uses
the current role retrieved from SQLite.

## Security Test Results

The following tests were performed locally:

| Test | Actual HTTP Response |
|---|---|
| Anonymous recipe update | 401 Unauthorized |
| Owner updates their recipe | 200 OK |
| Regular non-owner attempts recipe update | 403 Forbidden |
| Regular non-owner attempts recipe deletion | 403 Forbidden |
| Administrator updates another user's recipe | 200 OK |
| Administrator deletes another user's recipe | 204 No Content |
| Regular user updates own recipe | 200 OK |
| Regular user deletes own recipe | 204 No Content |
| Administrator reads another user's private recipe | 200 OK |
| Regular user reads own private recipe | 200 OK |
| Regular user reads another user's private recipe | 404 Not Found |
| Anonymous visitor reads private recipe | 404 Not Found |
| Anonymous visitor reads public recipe | 200 OK |
| Administrator lists recipes | 200 OK - all recipes |
| Regular user lists recipes | 200 OK - public and owned recipes |
| Anonymous visitor lists recipes | 200 OK - public recipes only |
| Registration with requested admin role | 201 Created - user role assigned |

Database verification confirmed that unauthorized update and deletion attempts did not modify or remove the targeted recipe.

Three legacy recipes with missing ownership were migrated to User ID 1. A subsequent ownership integrity check found zero recipes with missing or invalid owners.

## Notes

This project uses Flask's development server for local testing. It is not configured for production deployment.

Never commit JWT secrets, real passwords, or local database files containing user credentials.
