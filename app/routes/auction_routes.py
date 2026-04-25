"""
auction_routes.py

Handles auction-related HTTP routes.
"""

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session

from backend.mainauction import get_state, submit_bid
from backend.remote_controls.wallet import get_wallet_balance
from src.services.pricing_service import get_current_eth_usd_price

from db.repositories.auction_repository import AuctionRepository
from db.repositories.bid_repository import BidRepository
from db.repositories.user_repository import UserRepository
from db.repositories.watchlist_repository import WatchlistRepository


auction_bp = Blueprint("auction", __name__)


@auction_bp.route("/api/state/<int:auction_id>")
def api_state(auction_id):
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
        return jsonify({
            "ok": False,
            "error": "Failed to fetch auction state",
            "details": str(e),
        }), 500


@auction_bp.route("/auction/<int:auction_id>", methods=["GET", "POST"])
def detail(auction_id):
    auction_repo = AuctionRepository()
    bid_repo = BidRepository()
    user_repo = UserRepository()
    watchlist_repo = WatchlistRepository()

    raw_auction = auction_repo.get_auction_by_id(auction_id)

    if not raw_auction:
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
        "current_bid_usd": current_bid_usd,
    }

    raw_bids = bid_repo.get_bids_for_auction(auction_id)

    history = []
    for bid in raw_bids:
        history.append({
            "user": (bid[6][:10] + "...") if bid[6] else f"User {bid[2]}",
            "amount": f"{float(bid[3])} ETH",
            "time": bid[5].strftime("%Y-%m-%d %H:%M") if bid[5] else "Unknown",
            "status": "Verified" if bid[4] else "Pending",
        })

    if request.method == "POST":
        if "user_id" not in session:
            flash("You must be logged in to place a bid.", "warning")
            return redirect(url_for("auth.login"))

        new_bid = float(request.form.get("bid_amount", 0))
        bidder_id = session["user_id"]

        wallet_address = user_repo.get_wallet_address_by_user_id(bidder_id)

        if not wallet_address:
            flash("You must have a test wallet assigned before placing a bid.", "danger")
            return redirect(url_for("auction.detail", auction_id=auction_id))

        balance = get_wallet_balance(bidder_id)
        balance_eth = balance.get("eth") if balance else None

        if new_bid <= float(current_bid):
            flash(f"Bid must be higher than {auction['current_bid']} ETH.", "danger")
            return redirect(url_for("auction.detail", auction_id=auction_id))

        if balance_eth is not None and new_bid > float(balance_eth):
            flash(f"You only have {round(float(balance_eth), 4)} ETH available.", "danger")
            return redirect(url_for("auction.detail", auction_id=auction_id))

        try:
            submit_bid(auction_id, new_bid, wallet_address)
            success = bid_repo.submit_bid(auction_id, bidder_id, new_bid)

            if success:
                flash(f"Success! Your bid of {new_bid} ETH has been placed.", "success")
            else:
                flash("Bid reached blockchain but failed to save in the database.", "warning")

        except Exception:
            flash("Bid transaction failed. Please try again.", "danger")

        return redirect(url_for("auction.detail", auction_id=auction_id))

    is_watched = False

    if "user_id" in session:
        watchlist = watchlist_repo.get_user_watchlist(session["user_id"])
        is_watched = auction_id in watchlist

    return render_template(
        "detail.html",
        auction=auction,
        is_watched=is_watched,
        history=history,
        is_seller=is_seller,
    )