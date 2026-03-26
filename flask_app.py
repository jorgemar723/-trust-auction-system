from __future__ import annotations

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session

import os
from datetime import datetime, timezone
from db.run_sql_schema import run_sql_schema
from db.PostgresDB import PostgresDB
import bcrypt
from werkzeug.utils import secure_filename
from backend.mainauction import create_new_auction as deploy_auction

app = Flask(__name__)
app.secret_key = "trust_secret_key"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.before_request
def validate_session():
    if "user_id" in session:
        db = PostgresDB()
        db.connect()
        user = db.get_user_by_id(session["user_id"])
        db.close()
        if user is None:
            session.clear()


# Backend wiring: Flask -> backend.mainauction -> state.py -> Hardhat
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


def to_seconds(date_string: str) -> int:
    local_dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M")
    local_dt = local_dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    utc_dt = local_dt.astimezone(timezone.utc)
    return int(utc_dt.timestamp())


def error_json(code: str, message: str, details: str | None = None, http_status: int = 500):
    payload = {
        "ok": False,
        "error": {"code": code, "message": message},
    }
    if details:
        payload["details"] = details
    return jsonify(payload), http_status


@app.route("/")
def index():
    db = PostgresDB()
    db.connect()
    raw_auctions = db.get_auctions()
    db.close()

    formatted_auctions = []
    for row in raw_auctions:
        images = row[4]
        image_url = images[0] if images and len(images) > 0 else ""

        # DB fallback
        current_bid = row[9] if row[9] is not None else row[8]

        # Blockchain source of truth
        if get_state is not None:
            try:
                state = get_state(row[0])  # row[0] = auction_id
                if "highest_bid_eth" in state and state["highest_bid_eth"] is not None:
                    current_bid = state["highest_bid_eth"]
            except Exception as e:
                print(f"[WARN] Failed to fetch chain state for auction {row[0]}: {e}")

        formatted_auctions.append(
            {
                "id": row[0],
                "title": row[2],
                "description": row[3],
                "image": image_url,
                "current_bid": float(current_bid),
            }
        )

    return render_template("index.html", auctions=formatted_auctions)


@app.route("/auction/<int:auction_id>", methods=["GET", "POST"])
def detail(auction_id):
    db = PostgresDB()
    db.connect()
    raw_auction = db.get_auction_by_id(auction_id)

    if not raw_auction:
        db.close()
        return "Auction not found", 404

    images = raw_auction[4]
    current_bid = raw_auction[9] if raw_auction[9] is not None else raw_auction[8]

    # Blockchain source of truth
    if get_state is not None:
        try:
            state = get_state(auction_id)
            if "highest_bid_eth" in state and state["highest_bid_eth"] is not None:
                current_bid = state["highest_bid_eth"]
        except Exception as e:
            print(f"[WARN] Failed to fetch chain state for auction {auction_id}: {e}")

    auction = {
        "id": raw_auction[0],
        "title": raw_auction[2],
        "description": raw_auction[3],
        "images": images if images else [],
        "image": images[0] if images and len(images) > 0 else "",
        "current_bid": float(current_bid),
    }

    raw_bids = db.get_bids_for_auction(auction_id)
    history = []
    for bid in raw_bids:
        history.append(
            {
                "user": (bid[6][:10] + "...") if bid[6] else f"User {bid[2]}",
                "amount": f"{float(bid[3])} ETH",
                "time": bid[5].strftime("%Y-%m-%d %H:%M") if bid[5] else "Unknown",
                "status": "Verified" if bid[4] else "Pending",
            }
        )

    if request.method == "POST":
        if "user_id" not in session:
            flash("You must be logged in to place a bid.", "warning")
            db.close()
            return redirect(url_for("login"))

        bid_raw = request.form.get("bid_amount", "0").strip()

        try:
            new_bid = float(bid_raw)
        except ValueError:
            flash("Bid amount must be a valid number.", "danger")
            db.close()
            return redirect(url_for("detail", auction_id=auction_id))

        if submit_bid is None:
            flash("Blockchain bidding backend is unavailable.", "danger")
            db.close()
            return redirect(url_for("detail", auction_id=auction_id))

        try:
            result = submit_bid(auction_id, new_bid)

            # Optional DB sync after on-chain success so bid history/watchlist stay useful
            db.submit_bid(auction_id, session["user_id"], new_bid)

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

        db.close()
        return redirect(url_for("detail", auction_id=auction_id))

    is_watched = False
    if "user_id" in session:
        watchlist = db.get_user_watchlist(session["user_id"])
        is_watched = auction_id in watchlist

    db.close()
    return render_template("detail.html", auction=auction, is_watched=is_watched, history=history)


@app.route("/watchlist")
def view_watchlist():
    if "user_id" not in session:
        flash("You must be logged in to view your watchlist.", "warning")
        return redirect(url_for("login"))

    db = PostgresDB()
    db.connect()
    watchlist_ids = db.get_user_watchlist(session["user_id"])

    watched_items = []
    for w_id in watchlist_ids:
        row = db.get_auction_by_id(w_id)
        if row:
            images = row[4]
            image_url = images[0] if images and len(images) > 0 else ""
            current_bid = row[9] if row[9] is not None else row[8]

            # Blockchain source of truth
            if get_state is not None:
                try:
                    state = get_state(row[0])
                    if "highest_bid_eth" in state and state["highest_bid_eth"] is not None:
                        current_bid = state["highest_bid_eth"]
                except Exception as e:
                    print(f"[WARN] Failed to fetch chain state for watchlist auction {row[0]}: {e}")

            watched_items.append(
                {
                    "id": row[0],
                    "title": row[2],
                    "description": row[3],
                    "image": image_url,
                    "current_bid": float(current_bid),
                }
            )

    db.close()
    return render_template("watchlist.html", auctions=watched_items)


@app.route("/toggle-watchlist/<int:auction_id>")
def toggle_watchlist(auction_id):
    if "user_id" not in session:
        flash("You must be logged in to manage your watchlist.", "warning")
        return redirect(url_for("login"))

    db = PostgresDB()
    db.connect()
    watchlist = db.get_user_watchlist(session["user_id"])

    if auction_id in watchlist:
        db.remove_from_watchlist(session["user_id"], auction_id)
        flash("Removed from watchlist.", "info")
    else:
        db.add_to_watchlist(session["user_id"], auction_id)
        flash("Added to watchlist.", "success")

    db.close()
    return redirect(request.referrer or url_for("index"))


@app.route("/api/state/<int:auction_id>")
def api_state(auction_id):
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


# ================= CREATE AUCTION =================
@app.route("/auction/create", methods=["GET", "POST"])
def create_auction():
    if "user_id" not in session:
        flash("You must be logged in to create an auction.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        starting_bid = request.form.get("starting_bid")
        expires_at = request.form.get("expires_at")

        images = request.files.getlist("images")
        image_urls = []

        for image in images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                image.save(image_path)
                image_urls.append(f"uploads/{filename}")

        created_at = datetime.now(timezone.utc)
        seller_id = session["user_id"]

        result_seconds = to_seconds(expires_at) - int(created_at.timestamp())
        print(f"Creating auction with duration {result_seconds} seconds")

        if result_seconds <= 0:
            flash("Invalid auction time. Please select a future time.", "danger")
            return redirect(url_for("create_auction"))

        result = deploy_auction(result_seconds)

        contract_address = result["auction_address"]
        tx_hash = result["tx_hash"]

        db = PostgresDB()
        db.connect()
        success = db.create_auction(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_urls=image_urls,
            created_at=created_at,
            expires_at=expires_at,
            seller_id=seller_id,
            contract_address=contract_address,
            tx_hash=tx_hash,
        )

        db.close()

        if success:
            flash("Auction created successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Failed to create auction. Please try again.", "danger")

    return render_template("create_auction.html")


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
    app.run(port=8000, debug=True)