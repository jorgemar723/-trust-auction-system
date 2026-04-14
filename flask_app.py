from __future__ import annotations

import os
from datetime import datetime, timezone
from db.run_sql_schema import run_sql_schema
from db.PostgresDB import PostgresDB
import bcrypt
from werkzeug.utils import secure_filename
from backend.mainauction import create_new_auction as deploy_auction
from src.services.pricing_service import get_current_eth_usd_price
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session

app = Flask(__name__)
app.secret_key = "trust_secret_key"

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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


def parse_local_datetime_to_utc(date_string: str) -> datetime:
    # Browser sends a naive local datetime string like "2026-04-08T19:30"
    local_dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M")

    # Attach the current local timezone
    local_tz = datetime.now().astimezone().tzinfo
    local_dt = local_dt.replace(tzinfo=local_tz)

    # Convert to UTC for consistent storage and blockchain timing
    return local_dt.astimezone(timezone.utc)


def to_seconds(date_string: str) -> int:
    utc_dt = parse_local_datetime_to_utc(date_string)
    return int(utc_dt.timestamp())


def format_time_remaining(expires_at):
    if not expires_at:
        return "Ended"

    now = datetime.now().astimezone()

    # Handle string timestamps safely
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            return "Ended"

    # If DB time is naive, assume local timezone
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=now.tzinfo)

    diff = expires_at - now
    total_seconds = int(diff.total_seconds())

    if total_seconds <= 0:
        return "Ended"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"


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

        for row in raw_auctions:
            images = row[4]
            image_url = images[0] if images and len(images) > 0 else ""

            current_bid = row[9] if row[9] is not None else row[8]

            formatted_auctions.append({
                "id": row[0],
                "title": row[2],
                "description": row[3],
                "image": image_url,
                "current_bid": float(current_bid),
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

# ================= AUCTION DETAILS =================
@app.route("/auction/<int:auction_id>", methods=["GET", "POST"])
def detail(auction_id):
    db = PostgresDB()
    db.connect()
    raw_auction = db.get_auction_by_id(auction_id)

    if not raw_auction:
        db.close()
        return "Auction not found", 404

    seller_id = raw_auction[1]
    is_seller = "user_id" in session and session["user_id"] == seller_id

    images = raw_auction[4]
    current_bid = raw_auction[9] if raw_auction[9] is not None else raw_auction[8]
    
    try:
        eth_price = get_current_eth_usd_price()
    except Exception:
        eth_price = None

    if eth_price is not None:
        current_bid_usd = round(float(current_bid) * float(eth_price), 2)
    else:
        current_bid_usd = None

    auction = {
        "id": raw_auction[0],
        "title": raw_auction[2],
        "description": raw_auction[3],
        "images": images if images else [],
        "image": images[0] if images and len(images) > 0 else "",
        "current_bid": float(current_bid),
        "current_bid_usd":(current_bid_usd)
    }

    raw_bids = db.get_bids_for_auction(auction_id)
    history = []
    for bid in raw_bids:
        history.append({
            "user": (bid[6][:10] + "...") if bid[6] else f"User {bid[2]}",
            "amount": f"{float(bid[3])} ETH",
            "time": bid[5].strftime("%Y-%m-%d %H:%M") if bid[5] else "Unknown",
            "status": "Verified" if bid[4] else "Pending"
        })

    if request.method == "POST":
        if "user_id" not in session:
            flash("You must be logged in to place a bid.", "warning")
            db.close()
            return redirect(url_for("login"))

        new_bid = float(request.form.get("bid_amount", 0))
        bidder_id = session["user_id"]

        wallet_address = db.get_wallet_address_by_user_id(bidder_id)
        if not wallet_address:
            db.close()
            flash("You must have a test wallet assigned before placing a bid.", "danger")
            return redirect(url_for("detail", auction_id=auction_id))

        try:
            submit_bid(auction_id, new_bid, wallet_address)
            success = db.submit_bid(auction_id, bidder_id, new_bid)

            if success:
                flash(f"Success! Your bid of {new_bid} ETH has been placed.", "success")
            else:
                flash("Bid reached blockchain but failed to save in the database.", "warning")

        except Exception as e:
            if _BackendAPIError is not None and isinstance(e, _BackendAPIError):
                error_text = f"{e.message} {e.details}" if e.details else e.message

                if (
                    "higher" in error_text.lower()
                    or "low" in error_text.lower()
                    or "bid too low" in error_text.lower()
                    or "not high enough" in error_text.lower()
                    or "below starting bid" in error_text.lower()
                ):
                    flash(f"Bid failed. You must bid higher than {auction['current_bid']} ETH.", "danger")
                else:
                    flash(f"Bid failed: {e.message}", "danger")
            else:
                flash("Bid transaction failed. Please try again.", "danger")

        db.close()
        return redirect(url_for("detail", auction_id=auction_id))

    is_watched = False
    if "user_id" in session:
        watchlist = db.get_user_watchlist(session["user_id"])
        is_watched = auction_id in watchlist

    db.close()
    return render_template("detail.html", auction=auction, is_watched=is_watched, history=history, is_seller=is_seller)


# ================= WATCHLIST =================
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

            watched_items.append({
                "id": row[0],
                "title": row[2],
                "description": row[3],
                "image": image_url,
                "current_bid": float(current_bid),
                "time_remaining": format_time_remaining(row[6])
            })

    db.close()
    return render_template("watchlist.html", auctions=watched_items)


# ================= TOGGLE WATCHLIST =================
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


# ================= MY AUCTIONS =================
@app.route("/my-auctions")
def my_auctions():
    if "user_id" not in session:
        flash("You must be logged in to view your auctions.", "warning")
        return redirect(url_for("login"))

    db = PostgresDB()
    db.connect()
    raw_auctions = db.get_auctions_by_seller_id(session["user_id"])
    db.close()

    formatted_auctions = []
    for row in raw_auctions:
        images = row[4]
        image_url = images[0] if images and len(images) > 0 else ""
        current_bid = row[9] if row[9] is not None else row[8]

        formatted_auctions.append({
            "id": row[0],
            "title": row[2],
            "description": row[3],
            "image": image_url,
            "current_bid": float(current_bid),
            "time_remaining": format_time_remaining(row[6])
        })

    return render_template("my_auctions.html", auctions=formatted_auctions)


# ================= AUCTION STATE =================
@app.route("/api/state/<int:auction_id>")
def api_state(auction_id):
    """
    Returns live auction state from the backend wiring:
    Flask -> backend.mainauction -> backend.state -> Hardhat
    """
    if get_state is None:
        return error_json(
            "BACKEND_IMPORT_FAILED",
            "Backend import failed.",
            _backend_import_error,
            500,
        )

    try:
        state = get_state(auction_id)
        
        try:
            eth_price = get_current_eth_usd_price()
        except Exception:
            eth_price = None
        
        highest_bid_eth = state.get("highest_bid_eth")
        
        if eth_price is not None and highest_bid_eth is not None:
            try:
                highest_bid_usd = highest_bid_eth * eth_price
            except Exception:
                highest_bid_usd = None
        else:
            highest_bid_usd = None
        
        state["highest_bid_usd"] = highest_bid_usd
        
        return jsonify({"ok": True, "data": state}), 200
    
    except Exception as e:
        print("STATE ERROR:", e)
        print("STATE ERROR DETAILS:", getattr(e, 'details', None))
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
        starting_bid = float(request.form.get("starting_bid", 0))
        expires_at = request.form.get("expires_at")

        images = request.files.getlist("images")
        image_urls = []

        for image in images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                image_urls.append(f"uploads/{filename}")

        created_at = datetime.now(timezone.utc)
        seller_id = session["user_id"]

        expires_at_utc = parse_local_datetime_to_utc(expires_at)
        result_seconds = int(expires_at_utc.timestamp()) - int(created_at.timestamp())

        if result_seconds <= 0:
            flash("Invalid auction time. Please select a future time.", "danger")
            return redirect(url_for("create_auction"))

        if starting_bid <= 0:
            flash("Starting bid must be a positive value.", "danger")
            return redirect(url_for("create_auction"))


        db = PostgresDB()
        db.connect()
        wallet_address = db.get_wallet_address_by_user_id(seller_id)

        if not wallet_address:
            db.close()
            flash("You must have a test wallet assigned before creating an auction.", "danger")
            return redirect(url_for("create_auction"))

        result = deploy_auction(result_seconds, wallet_address, starting_bid)
        contract_address = result["auction_address"]
        tx_hash = result["tx_hash"]

        success = db.create_auction(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_urls=image_urls,
            created_at=created_at,
            expires_at=expires_at_utc,
            seller_id=seller_id,
            contract_address=contract_address,
            tx_hash=tx_hash
        )

        db.close()

        if success:
            flash("Auction created successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Failed to create auction. Please try again.", "danger")

    return render_template("create_auction.html")


# ================= EDIT AUCTION =================
@app.route("/auction/<int:auction_id>/edit", methods=["GET", "POST"])
def edit_auction(auction_id):
    if "user_id" not in session:
        flash("You must be logged in to edit an auction.", "warning")
        return redirect(url_for("login"))

    db = PostgresDB()
    db.connect()
    raw_auction = db.get_auction_by_id(auction_id)

    if not raw_auction:
        db.close()
        flash("Auction not found.", "danger")
        return redirect(url_for("index"))

    seller_id = raw_auction[1]
    if session["user_id"] != seller_id:
        db.close()
        flash("You are not authorized to edit this auction.", "danger")
        return redirect(url_for("detail", auction_id=auction_id))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        existing_images = raw_auction[4] if raw_auction[4] else []
        images_to_delete = request.form.getlist("delete_images")

        updated_images = [img for img in existing_images if img not in images_to_delete]

        for image_path_to_delete in images_to_delete:
            try:
                full_path = os.path.join(app.root_path, 'static', image_path_to_delete)
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                print(f"Error deleting file {full_path}: {e}")

        new_images = request.files.getlist("images")
        for image in new_images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                updated_images.append(f"uploads/{filename}")

        success = db.update_auction(
            auction_id=auction_id,
            title=title,
            description=description,
            image_urls=updated_images
        )
        db.close()

        if success:
            flash("Auction updated successfully!", "success")
            return redirect(url_for("detail", auction_id=auction_id))
        else:
            flash("Failed to update auction. Please try again.", "danger")
            return redirect(url_for("edit_auction", auction_id=auction_id))

    auction = {
        "id": raw_auction[0],
        "title": raw_auction[2],
        "description": raw_auction[3],
        "images": raw_auction[4] if raw_auction[4] else []
    }
    db.close()
    return render_template("edit_auction.html", auction=auction)


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