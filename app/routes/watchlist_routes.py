"""
watchlist_routes.py

Purpose:
    Handles watchlist-related HTTP routes.

    This module allows users to view and manage their saved auctions.

Responsibilities:
    - View watchlist
    - Add auctions to watchlist
    - Remove auctions from watchlist

System Position:

    Flask HTTP Layer (modular routes)
        ├── auction_routes.py
        ├── auction_create_routes.py
        ├── watchlist_routes.py  ← THIS FILE
        ├── user_auction_routes.py
        └── auth_routes.py

    This module is part of the Flask routing layer and interacts
    with the database to manage user watchlists.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from db.PostgresDB import PostgresDB
from app.utils.datetime_utils import format_time_remaining

watchlist_bp = Blueprint("watchlist", __name__)

# ================= WATCHLIST =================
@watchlist_bp.route("/watchlist")
def view_watchlist():
    if "user_id" not in session:
        flash("You must be logged in to view your watchlist.", "warning")
        return redirect(url_for("auth.login"))

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
@watchlist_bp.route("/toggle-watchlist/<int:auction_id>")
def toggle_watchlist(auction_id):
    if "user_id" not in session:
        flash("You must be logged in to manage your watchlist.", "warning")
        return redirect(url_for("auth.login"))

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
    return redirect(request.referrer) if request.referrer else redirect(url_for("index"))