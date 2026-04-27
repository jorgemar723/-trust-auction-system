"""
auction_routes.py

Handles auction-related HTTP routes.
"""

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
from src.services.auction_service import AuctionService

from db.repositories.auction_repository import AuctionRepository
from db.repositories.bid_repository import BidRepository
from db.repositories.user_repository import UserRepository
from db.repositories.watchlist_repository import WatchlistRepository


auction_bp = Blueprint("auction", __name__)


@auction_bp.route("/api/state/<int:auction_id>")
def api_state(auction_id):
    try:
        state = AuctionService.get_auction_state_with_usd(auction_id)
        return jsonify({"ok": True, "data": state}), 200

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": "Failed to fetch auction state",
            "details": str(e),
        }), 500


@auction_bp.route("/auction/<int:auction_id>", methods=["GET", "POST"])
def detail(auction_id):
    if request.method == "POST":
        if "user_id" not in session:
            flash("You must be logged in to place a bid.", "warning")
            return redirect(url_for("auth.login"))

        new_bid = float(request.form.get("bid_amount", 0))
        bidder_id = session["user_id"]

        result = AuctionService.place_bid(auction_id, bidder_id, new_bid)
        if result["success"]:
            flash(result["message"], "success")
        else:
            flash(result["error"], "danger")

        return redirect(url_for("auction.detail", auction_id=auction_id))

    details = AuctionService.get_auction_details(auction_id, session.get("user_id"))
    if not details:
        return "Auction not found", 404
        
    return render_template(
        "detail.html", 
        auction=details["auction"], 
        is_watched=details["is_watched"], 
        history=details["history"], 
        is_seller=details["is_seller"]
    )