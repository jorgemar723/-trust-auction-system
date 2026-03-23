from __future__ import annotations

from db.run_sql_schema import run_sql_schema
from db.PostgresDB import PostgresDB
import bcrypt

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session

app = Flask(__name__)
app.secret_key = "trust_secret_key"


# Backend wiring: Flask -> backend.mainauction -> remote_controls -> Hardhat
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


# Mock catalog data for page content only
# These IDs must match real backend auction IDs in _AUCTION_REGISTRY
AUCTIONS = [
    {
        "id": 1,
        "title": "Vintage Rolex Submariner",
        "current_bid": 4.0,
        "image": "Rolex.jpg",
        "description": "Certified authentic 1970s diving watch.",
    },
    {
        "id": 2,
        "title": "Unopened 1st Ed. Charizard",
        "current_bid": 12.5,
        "image": "Charizard.jpg",
        "description": "Mint condition, PSA 10 candidate.",
    },
    {
        "id": 3,
        "title": "Bored Ape Yacht Club #772",
        "current_bid": 65.0,
        "image": "NFT.jpg",
        "description": "Rare gold fur trait. Smart contract verified.",
    },
]

WATCHLIST = []

@app.route("/")
def index():
    hydrated_auctions = []

    for auction in AUCTIONS:
        auction_copy = auction.copy()  # avoid mutating original list

        if get_state is not None:
            try:
                state = get_state(auction["id"])
                auction_copy["current_bid"] = state["highest_bid_eth"]
                auction_copy["status"] = state["status"]
            except Exception:
                # If something fails, fallback to existing value
                pass

        hydrated_auctions.append(auction_copy)

    return render_template("index.html", auctions=hydrated_auctions)


@app.route("/auction/<int:auction_id>", methods=["GET", "POST"])
def detail(auction_id):
    auction = next((a for a in AUCTIONS if a["id"] == auction_id), None)
    if not auction:
        return "Auction not found", 404

    history = [
        {"user": "0x71C...a2E", "amount": "4.1 ETH", "time": "2 hours ago", "status": "Verified"},
        {"user": "0x32B...f11", "amount": "3.8 ETH", "time": "5 hours ago", "status": "Verified"},
        {"user": "0x99A...c43", "amount": "3.5 ETH", "time": "1 day ago", "status": "Verified"},
    ]

    live_state = None
    state_error = None

    # Load live blockchain state for display
    if get_state is not None:
        try:
            live_state = get_state(auction_id)
            auction["current_bid"] = live_state["highest_bid_eth"]
        except Exception as e:
            if _BackendAPIError is not None and isinstance(e, _BackendAPIError):
                state_error = f"{e.code}: {e.message}"
            else:
                state_error = str(e)

    if request.method == "POST":
        bid_raw = request.form.get("bid_amount", "0")

        if new_bid > auction["current_bid"]:
            auction["current_bid"] = new_bid
            flash(f"Success! Your bid of {new_bid} ETH has been placed.", "success")
        else:
            flash(f"Bid failed. You must bid higher than {auction['current_bid']} ETH.", "danger")

        if submit_bid is None:
            flash("Backend bid function is unavailable.", "danger")
            return redirect(url_for("detail", auction_id=auction_id))

        try:
            result = submit_bid(auction_id, new_bid)
            flash(
                f"Success! Your bid of {new_bid} ETH has been placed. Tx: {result['tx_hash']}",
                "success",
            )
        except Exception as e:
            if _BackendAPIError is not None and isinstance(e, _BackendAPIError):
                details = f" ({e.details})" if getattr(e, "details", None) else ""
                flash(f"Bid failed: {e.message}{details}", "danger")
            else:
                flash(f"Bid failed: {str(e)}", "danger")

        return redirect(url_for("detail", auction_id=auction_id))

    is_watched = auction_id in WATCHLIST
    return render_template(
        "detail.html",
        auction=auction,
        is_watched=is_watched,
        history=history,
        live_state=live_state,
        state_error=state_error,
    )


@app.route("/watchlist")
def view_watchlist():
    watched_items = [a for a in AUCTIONS if a["id"] in WATCHLIST]
    return render_template("watchlist.html", auctions=watched_items)


@app.route("/toggle-watchlist/<int:auction_id>")
def toggle_watchlist(auction_id):
    if auction_id in WATCHLIST:
        WATCHLIST.remove(auction_id)
        flash("Removed from watchlist.", "info")
    else:
        WATCHLIST.append(auction_id)
        flash("Added to watchlist.", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/api/state")
def api_state():
    if get_state is None:
        return error_json(
            "BACKEND_IMPORT_FAILED",
            "Backend import failed.",
            _backend_import_error,
            500,
        )

    try:
        state = get_state(auction_id)
        return jsonify({"ok": True, "data": state}), 200
    except Exception as e:
        if _BackendAPIError is not None and isinstance(e, _BackendAPIError):
            return error_json(e.code, e.message, e.details, e.http_status)

        return error_json(
            "UNEXPECTED_ERROR",
            "Unexpected server error.",
            str(e),
            500,
        )


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
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
            return redirect(url_for("register"))

    return render_template("register.html")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
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
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))


# ================= START APP =================
if __name__ == "__main__":
    run_sql_schema("db/schema.sql")
    app.run(port=8000, debug=True)
