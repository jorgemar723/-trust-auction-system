"""
watchlist_routes.py

Purpose:
    Handles watchlist-related HTTP routes.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from src.services.watchlist_service import WatchlistService


watchlist_bp = Blueprint("watchlist", __name__)


@watchlist_bp.route("/watchlist")
def view_watchlist():
    if "user_id" not in session:
        flash("You must be logged in to view your watchlist.", "warning")
        return redirect(url_for("auth.login"))

    watched_items = WatchlistService.get_user_watchlist_formatted(session["user_id"])
    return render_template("watchlist.html", auctions=watched_items)

# ================= TOGGLE WATCHLIST =================
@watchlist_bp.route("/toggle-watchlist/<int:auction_id>")
def toggle_watchlist(auction_id):
    if "user_id" not in session:
        flash("You must be logged in to manage your watchlist.", "warning")
        return redirect(url_for("auth.login"))

    result = WatchlistService.toggle_watchlist(session["user_id"], auction_id)
    if result["status"] == "removed":
        flash(result["message"], "info")
    else:
        flash(result["message"], "success")
        
    return redirect(request.referrer) if request.referrer else redirect(url_for("index"))