# TRUST Project – User Database Model

Author: Kristian Parra
Branch: feature/PROJ-52-password-hashing

---

# Overview

The TRUST project uses a SQLite database (`db/trust.db`) to store user account information.
User data is stored in the `users` table defined in `db/schema.sql`.

The system supports:

* User registration
* Email validation
* Duplicate email prevention
* Password hashing (secure storage)

---

# Database Location

Database file:

```
db/trust.db
```

Schema file:

```
db/schema.sql
```

Registration code:

```
src/database/register_user.py
```

Test script:

```
src/database/test_register.py
```

---

# Users Table Structure

| Field         | Type    | Description                     |
| ------------- | ------- | ------------------------------- |
| id            | INTEGER | Unique user ID (Primary Key)    |
| email         | TEXT    | User email (must be unique)     |
| password_hash | TEXT    | Hashed password (NOT plaintext) |
| created_at    | TEXT    | Timestamp when account created  |
| updated_at    | TEXT    | Timestamp when last updated     |
| is_active     | INTEGER | 1 = active, 0 = disabled        |

---

# Features Implemented

## User Registration

Users can register using:

```
python3 src/database/test_register.py
```

Example:

```
Email: test@email.com
Password: MyPassword123
SUCCESS: User registered
```

---

## Email Validation

The system validates:

* Proper email format
* Duplicate emails not allowed

Example duplicate:

```
ERROR: Email already exists
```

---

## Password Hashing (PROJ-52)

Passwords are NOT stored in plaintext.

Passwords are hashed using bcrypt before being stored.

Example database entry:

```
$2b$12$KIXQExampleHashValueHere
```

This improves security and protects user credentials.

---

# How Registration Works

Flow:

1. User enters email and password
2. Email format is validated
3. Password is hashed
4. Data is inserted into SQLite database
5. Database saves user permanently

---

# How to Test Registration

Run:

```
python3 src/database/test_register.py
```

Enter:

```
Email: your@email.com
Password: yourpassword
```

---

# How to View Users in Database

Open SQLite:

```
sqlite3 db/trust.db
```

Show tables:

```
.tables
```

Show all users:

```
SELECT * FROM users;
```

Exit:

```
.exit
```

---

# Example Database Output

Example:

```
1 | test@email.com | $2b$12$hashedpassword | 2026-02-25 | 2026-02-25 | 1
```

---

# Security Notes

Passwords are stored as hashes only.

Plaintext passwords are never saved.

This protects users if the database is compromised.

---

# Summary

The user database supports:

* Secure registration
* Email validation
* Duplicate prevention
* Password hashing
* Persistent storage

This completes:

PROJ-48 – User Registration
PROJ-51 – Email Validation
PROJ-52 – Password Hashing

---
