from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.services.auction_create_service import AuctionCreateService


auction_create_bp = Blueprint("auction_create", __name__)


@auction_create_bp.route("/auction/create", methods=["GET", "POST"])
def create_auction():
    if "user_id" not in session:
        flash("You must be logged in to create an auction.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        starting_bid = float(request.form.get("starting_bid", 0))
        expires_at = request.form.get("expires_at")
        images = request.files.getlist("images")

        result = AuctionCreateService.create_auction(
            user_id=session["user_id"],
            title=title,
            description=description,
            starting_bid=starting_bid,
            expires_at=expires_at,
            images=images
        )

        if result["success"]:
            flash("Auction created successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash(result["error"], "danger")
            return redirect(url_for("auction_create.create_auction"))

        flash("Failed to create auction. Please try again.", "danger")

    return render_template("create_auction.html")


@auction_create_bp.route("/auction/<int:auction_id>/edit", methods=["GET", "POST"])
def edit_auction(auction_id):
    if "user_id" not in session:
        flash("You must be logged in to edit an auction.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        images_to_delete = request.form.getlist("delete_images")
        new_images = request.files.getlist("images")

        result = AuctionCreateService.edit_auction(
            auction_id=auction_id,
            user_id=user_id,
            title=title,
            description=description,
            images_to_delete=images_to_delete,
            new_images=new_images
        )

        if result["success"]:
            flash("Auction updated successfully!", "success")
            return redirect(url_for("auction.detail", auction_id=auction_id))
        else:
            flash(result["error"], "danger")
            return redirect(url_for("auction_create.edit_auction", auction_id=auction_id))

    result = AuctionCreateService.get_auction_for_edit(auction_id, user_id)
    if not result["success"]:
        flash(result["error"], "danger")
        if result.get("unauthorized"):
            return redirect(url_for("auction.detail", auction_id=auction_id))
        return redirect(url_for("index"))

    return render_template("edit_auction.html", auction=result["auction"])