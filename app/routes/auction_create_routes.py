from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.mainauction import create_new_auction as deploy_auction
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from app.utils.datetime_utils import parse_local_datetime_to_utc
from app.utils.s3_utils import upload_file_to_s3, delete_file_from_s3
from db.repositories.user_repository import UserRepository
from db.repositories.auction_repository import AuctionRepository
import os


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
        image_urls = []
        bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")

        # Local/demo-safe image handling:
        # If S3 is not configured, skip images instead of blocking auction creation.
        for image in images:
            if image and image.filename:
                if not bucket_name:
                    flash("Image upload skipped because S3 is not configured.", "warning")
                    continue

                image_url = upload_file_to_s3(image, bucket_name)

                if image_url:
                    image_urls.append(image_url)
                else:
                    flash(f"Failed to upload image: {secure_filename(image.filename)}", "danger")
                    return redirect(url_for("auction_create.create_auction"))

        created_at = datetime.now(timezone.utc)
        seller_id = session["user_id"]

        expires_at_utc = parse_local_datetime_to_utc(expires_at)
        result_seconds = int(expires_at_utc.timestamp()) - int(created_at.timestamp())

        if result_seconds <= 0:
            flash("Invalid auction time. Please select a future time.", "danger")
            return redirect(url_for("auction_create.create_auction"))

        if starting_bid <= 0:
            flash("Starting bid must be a positive value.", "danger")
            return redirect(url_for("auction_create.create_auction"))

        user_repo = UserRepository()
        auction_repo = AuctionRepository()

        wallet_address = user_repo.get_wallet_address_by_user_id(seller_id)

        if not wallet_address:
            flash("You must have a test wallet assigned before creating an auction.", "danger")
            return redirect(url_for("auction_create.create_auction"))

        result = deploy_auction(result_seconds, wallet_address, starting_bid)

        contract_address = result["auction_address"]
        tx_hash = result["tx_hash"]

        success = auction_repo.create_auction(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_urls=image_urls,
            created_at=created_at,
            expires_at=expires_at_utc,
            seller_id=seller_id,
            contract_address=contract_address,
            tx_hash=tx_hash,
        )

        if success:
            flash("Auction created successfully!", "success")
            return redirect(url_for("index"))

        flash("Failed to create auction. Please try again.", "danger")

    return render_template("create_auction.html")


@auction_create_bp.route("/auction/<int:auction_id>/edit", methods=["GET", "POST"])
def edit_auction(auction_id):
    if "user_id" not in session:
        flash("You must be logged in to edit an auction.", "warning")
        return redirect(url_for("auth.login"))

    auction_repo = AuctionRepository()
    raw_auction = auction_repo.get_auction_by_id(auction_id)

    if not raw_auction:
        flash("Auction not found.", "danger")
        return redirect(url_for("index"))

    seller_id = raw_auction[1]

    if session["user_id"] != seller_id:
        flash("You are not authorized to edit this auction.", "danger")
        return redirect(url_for("auction.detail", auction_id=auction_id))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        existing_images = raw_auction[4] if raw_auction[4] else []
        bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")

        images_to_delete = request.form.getlist("delete_images")
        updated_images = [img for img in existing_images if img not in images_to_delete]

        if images_to_delete and not bucket_name:
            flash("Image deletion skipped because S3 is not configured.", "warning")
        elif bucket_name:
            for url_to_delete in images_to_delete:
                delete_file_from_s3(url_to_delete, bucket_name)

        new_images = request.files.getlist("images")

        for image in new_images:
            if image and image.filename:
                if not bucket_name:
                    flash("New image upload skipped because S3 is not configured.", "warning")
                    continue

                image_url = upload_file_to_s3(image, bucket_name)

                if image_url:
                    updated_images.append(image_url)
                else:
                    flash(f"Failed to upload new image: {secure_filename(image.filename)}", "danger")
                    return redirect(url_for("auction_create.edit_auction", auction_id=auction_id))

        success = auction_repo.update_auction(
            auction_id=auction_id,
            title=title,
            description=description,
            image_urls=updated_images,
        )

        if success:
            flash("Auction updated successfully!", "success")
            return redirect(url_for("auction.detail", auction_id=auction_id))

        flash("Failed to update auction. Please try again.", "danger")
        return redirect(url_for("auction_create.edit_auction", auction_id=auction_id))

    auction = {
        "id": raw_auction[0],
        "title": raw_auction[2],
        "description": raw_auction[3],
        "images": raw_auction[4] if raw_auction[4] else [],
    }

    return render_template("edit_auction.html", auction=auction)