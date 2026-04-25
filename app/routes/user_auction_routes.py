"""
user_auction_routes.py

Purpose:
    Handles routes related to auctions owned by the current user.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session
from db.repositories.auction_repository import AuctionRepository
from app.utils.datetime_utils import format_time_remaining


user_auction_bp = Blueprint("user_auction", __name__)


@user_auction_bp.route("/my-auctions")
def my_auctions():
    if "user_id" not in session:
        flash("You must be logged in to view your auctions.", "warning")
        return redirect(url_for("auth.login"))

    auction_repo = AuctionRepository()
    raw_auctions = auction_repo.get_auctions_by_seller_id(session["user_id"])

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
            "time_remaining": format_time_remaining(row[6]),
        })

    return render_template("my_auctions.html", auctions=formatted_auctions)