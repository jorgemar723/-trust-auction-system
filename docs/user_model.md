# TRUST Project – User Database Model

Author: Kristian Parra  
Branch: PROJ-49-user-database-structure  

---

# Overview

This document describes the structure and usage of the user database for the TRUST application.

The database is implemented using SQLite and stored locally as:

db/trust.db

The structure of the database is defined in:

db/schema.sql

The schema acts as a blueprint, and the trust.db file stores the actual user data.

---

# Users Table Structure

The users table stores account information for each registered user.

Fields:

user_id
- INTEGER
- Primary Key
- Automatically increments
- Unique identifier for each user

email
- TEXT
- Required
- Must be UNIQUE
- Used for login

password_hash
- TEXT
- Required
- Stores encrypted password

created_at
- TEXT
- Automatically generated timestamp

updated_at
- TEXT
- Automatically generated timestamp

is_active
- INTEGER
- Default: 1
- 1 = active
- 0 = disabled

---

# Creating the Database

Run this command in the terminal:

sqlite3 db/trust.db < db/schema.sql

This creates the trust.db file and users table.

---

# Viewing the Database

Open the database:

sqlite3 db/trust.db

---

# Show all tables

.tables

Expected output:

users

---

# View table structure

.schema users

---

# View all users

SELECT * FROM users;

---

# Add a test user

INSERT INTO users (email, password_hash)
VALUES ('test@email.com', 'hashedpassword');

---

# View users again

SELECT * FROM users;

Example output:

1|test@email.com|hashedpassword|2026-02-20|2026-02-20|1

---

# Exit database

.exit

---

# Future Use

Python will connect to trust.db to:

- Register users
- Authenticate users
- Retrieve user data
- Connect users to blockchain wallet addresses

---

# Summary

schema.sql → defines structure

trust.db → stores actual data

Python → interacts with database