"""
flask_app.py

Purpose:
    Application entry point for the Flask server.

    This file initializes the Flask app, registers all route Blueprints,
    and defines global configuration shared across the application.

Responsibilities:
    - Initialize Flask app instance
    - Register Blueprints (modular route components)
    - Configure application settings
    - Define global hooks (e.g., context processors, session validation)

System Position:

    Flask Application Entry Point ← THIS FILE
        ↓
    Flask HTTP Layer (Blueprints)
        ├── auction_routes.py
        ├── auction_create_routes.py
        ├── watchlist_routes.py
        ├── user_auction_routes.py
        └── auth_routes.py

    Acts as the root of the HTTP layer and coordinates all route modules.
"""

from __future__ import annotations

import os
from db.PostgresDB import PostgresDB
from werkzeug.utils import secure_filename
from src.services.pricing_service import get_current_eth_usd_price
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from backend.remote_controls.wallet import get_wallet_balance
from app.routes.auction_routes import auction_bp
from app.routes.auction_create_routes import auction_create_bp
from app.utils.datetime_utils import format_time_remaining
from app.routes.watchlist_routes import watchlist_bp
from app.routes.user_auction_routes import user_auction_bp
from app.routes.auth_routes import auth_bp

app = Flask(__name__)
app.secret_key = "trust_secret_key"

app.register_blueprint(auction_bp)
app.register_blueprint(auction_create_bp)
app.register_blueprint(watchlist_bp)
app.register_blueprint(user_auction_bp)
app.register_blueprint(auth_bp)

@app.before_request
def validate_session():
    # Ensure the user_id in the session is valid
    if 'user_id' in session:
        db = PostgresDB()
        db.connect()
        user = db.get_user_by_id(session['user_id'])
        db.close()
        if user is None:
            session.clear()


# Backend wiring (PROJ-38/39): Flask -> backend.mainauction -> state.py -> Hardhat
get_state = None
submit_bid = None
_backend_import_error = None
_BackendAPIError = None

try:
    from backend.mainauction import (
        get_state as _get_state,
        submit_bid as _submit_bid,
        BackendAPIError as _BackendAPIError,
    )

    get_state = _get_state
    submit_bid = _submit_bid
    _BackendAPIError = _BackendAPIError
except Exception as e:
    _backend_import_error = str(e)


def error_json(code: str, message: str, details: str | None = None, http_status: int = 500):
    payload = {
        "ok": False,
        "error": {"code": code, "message": message},
    }
    if details:
        payload["details"] = details
    return jsonify(payload), http_status


# ================= INDEX =================
@app.route("/")
def index():
    db = PostgresDB()
    db.connect()

    loading = False
    error_message = None
    formatted_auctions = []

    try:
        raw_auctions = db.get_auctions()

        try:
            eth_price = get_current_eth_usd_price()
        except Exception:
            eth_price = None

        for row in raw_auctions:
            images = row[4]
            image_url = images[0] if images and len(images) > 0 else ""

            current_bid = row[9] if row[9] is not None else row[8]

            current_bid_usd = None
            if eth_price is not None:
                try:
                    current_bid_usd = round(float(current_bid) * float(eth_price), 2)
                except Exception:
                    current_bid_usd = None

            formatted_auctions.append({
                "id": row[0],
                "title": row[2],
                "description": row[3],
                "image": image_url,
                "current_bid": float(current_bid),
                "current_bid_usd": current_bid_usd,
                "time_remaining": format_time_remaining(row[6])
            })

    except Exception as e:
        print("INDEX ERROR:", e)
        error_message = "Failed to load auctions."

    finally:
        db.close()

    return render_template(
        "index.html",
        auctions=formatted_auctions,
        loading=loading,
        error_message=error_message
    )

@app.context_processor
def inject_wallet_balance():
    wallet_balance = None
    eth_price = None
    
    if "user_id" in session:
        try:
            wallet_balance = get_wallet_balance(session["user_id"])
        except Exception:
            wallet_balance = None

    try:
        eth_price = get_current_eth_usd_price()
    except Exception:
        eth_price = None

    return {
        "wallet_balance": wallet_balance,
        "eth_price": eth_price
    }

# ================= START APP =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
