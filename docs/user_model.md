# TRUST User Model

## Overview

The TRUST platform supports secure user registration using SQLite. This module ensures:

* Valid email format
* No duplicate registrations
* Secure password hashing
* Automated unit test verification

User data is stored in:

```
db/trust.db
```

Using schema:

```
db/schema.sql
```

---

# Features Implemented

## 1. User Registration (PROJ-48)

Registers a new user with email and password.

Function:

```
register_user(email, password)
```

Behavior:

* Inserts new user into database
* Returns success message
* Prevents duplicate email registration

---

## 2. Email Validation (PROJ-51)

Registration validates email format before insertion.

Validation includes:

* Contains "@"
* Contains domain name
* Rejects invalid format

Example:

Valid:

```
user@email.com
```

Invalid:

```
useremail.com
```

Returns:

```
ERROR: Invalid email format
```

---

## 3. Password Hashing (PROJ-52)

Passwords are NEVER stored as plaintext.

Passwords are hashed using:

```
bcrypt
```

Example stored value:

```
$2b$12$KIXQ4...
```

Security benefits:

* Protects against database leaks
* Industry standard security
* Salt automatically included

Verification uses:

```
bcrypt.checkpw()
```

---

## 4. Unit Testing (PROJ-53)

Automated tests verify system works correctly.

Test cases include:

* Successful registration
* Invalid email rejection
* Duplicate email rejection
* Password stored as hash (not plaintext)

---

# How to Run Registration Manually

From project root:

```
python3 src/database/test_register.py
```

Example:

```
Email: test@email.com
Password: password123
SUCCESS: User registered
```

---

# How to Run Unit Tests

From project root:

```
python3 -m pytest
```

Expected result:

```
4 passed in X.XXs
```

---

# Database Location

```
db/trust.db
```

Table:

```
users
```

Columns:

| Column        | Description     |
| ------------- | --------------- |
| id            | User ID         |
| email         | User email      |
| password_hash | Hashed password |

---

# File Structure

```
trust/
│
├── db/
│   ├── trust.db
│   ├── schema.sql
│
├── src/database/
│   ├── register_user.py
│   ├── test_register.py
│
├── tests/
│   ├── test_registration.py
│
├── docs/
│   ├── user_model.md
```

---

# Summary of Security Features

| Feature              | Status   |
| -------------------- | -------- |
| Email Validation     | Complete |
| Duplicate Prevention | Complete |
| Password Hashing     | Complete |
| Unit Testing         | Complete |

---

# Author

Kristian Parra
Texas State University
CS3398 Software Engineering
TRUST Project
