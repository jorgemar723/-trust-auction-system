"""
watchlist_routes.py

Purpose:
    Handles watchlist-related HTTP routes.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session, request

from db.repositories.watchlist_repository import WatchlistRepository
from db.repositories.auction_repository import AuctionRepository

from app.utils.datetime_utils import format_time_remaining


watchlist_bp = Blueprint("watchlist", __name__)


@watchlist_bp.route("/watchlist")
def view_watchlist():
    if "user_id" not in session:
        flash("You must be logged in to view your watchlist.", "warning")
        return redirect(url_for("auth.login"))

    watchlist_repo = WatchlistRepository()
    auction_repo = AuctionRepository()

    watchlist_ids = watchlist_repo.get_user_watchlist(session["user_id"])

    watched_items = []

    for auction_id in watchlist_ids:
        row = auction_repo.get_auction_by_id(auction_id)

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
                "time_remaining": format_time_remaining(row[6]),
            })

    return render_template("watchlist.html", auctions=watched_items)


@watchlist_bp.route("/toggle-watchlist/<int:auction_id>")
def toggle_watchlist(auction_id):
    if "user_id" not in session:
        flash("You must be logged in to manage your watchlist.", "warning")
        return redirect(url_for("auth.login"))

    watchlist_repo = WatchlistRepository()

    user_id = session["user_id"]
    watchlist = watchlist_repo.get_user_watchlist(user_id)

    if auction_id in watchlist:
        watchlist_repo.remove_from_watchlist(user_id, auction_id)
        flash("Removed from watchlist.", "info")
    else:
        watchlist_repo.add_to_watchlist(user_id, auction_id)
        flash("Added to watchlist.", "success")

    return redirect(request.referrer) if request.referrer else redirect(url_for("index"))