"""
auth_routes.py

Purpose:
    Handles user authentication and session management.

    This module processes login, registration, and logout requests.
    It manages session state for authenticated users.

Responsibilities:
    - User registration
    - User login
    - User logout
    - Session management

System Position:

    Flask HTTP Layer (modular routes)
        ├── auction_routes.py
        ├── auction_create_routes.py
        ├── watchlist_routes.py
        ├── user_auction_routes.py
        └── auth_routes.py  ← THIS FILE

    This module is part of the Flask routing layer and handles
    authentication-related HTTP requests.

    Delegates data access to the database layer (PostgresDB).
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from db.PostgresDB import PostgresDB
import bcrypt

auth_bp = Blueprint("auth", __name__)

# ================= REGISTER =================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("register"))

        db = PostgresDB()
        db.connect()
        result = db.create_user(email, password)
        db.close()

        if result["success"]:
            session["user_id"] = result["user_id"]
            session["user_email"] = email
            flash("Account created successfully.", "success")
            return redirect(url_for("index"))
        else:
            flash(f"Registration failed: {result['error']}", "danger")
            return redirect(url_for("auth.register"))

    return render_template("register.html")

# ================= LOGIN =================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("login"))

        db = PostgresDB()
        db.connect()
        user = db.get_user_by_email(email)
        db.close()

        if not user:
            flash("No account found with that email.", "danger")
            return redirect(url_for("login"))

        user_id, user_email, password_hash = user

        if bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            session["user_id"] = user_id
            session["user_email"] = user_email
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Incorrect password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

# ================= LOGOUT =================
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))
