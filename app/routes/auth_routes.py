"""
auth_routes.py

Purpose:
    Handles user authentication and session management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from src.services.auth_service import AuthService


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("auth.register"))

        result = AuthService.register_user(email, password)
        
        if result["success"]:
            session["user_id"] = result["user_id"]
            session["user_email"] = email
            flash("Account created successfully.", "success")
            return redirect(url_for("index"))

        flash(f"Registration failed: {result['error']}", "danger")
        return redirect(url_for("auth.register"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("auth.login"))

        result = AuthService.login_user(email, password)
        
        if result["success"]:
            session["user_id"] = result["user_id"]
            session["user_email"] = result["user_email"]
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash(result["error"], "danger")
            return redirect(url_for("auth.login"))

        flash("Incorrect password.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))