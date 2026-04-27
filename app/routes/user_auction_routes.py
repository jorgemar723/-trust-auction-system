"""
user_auction_routes.py

Purpose:
    Handles routes related to auctions owned by the current user.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session
from src.services.user_auction_service import UserAuctionService


user_auction_bp = Blueprint("user_auction", __name__)


@user_auction_bp.route("/my-auctions")
def my_auctions():
    if "user_id" not in session:
        flash("You must be logged in to view your auctions.", "warning")
        return redirect(url_for("auth.login"))

    formatted_auctions = UserAuctionService.get_user_auctions_formatted(session["user_id"])
    
    return render_template("my_auctions.html", auctions=formatted_auctions)