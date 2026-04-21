from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from db.PostgresDB import PostgresDB
from backend.mainauction import create_new_auction as deploy_auction
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from app.utils.datetime_utils import parse_local_datetime_to_utc
import os

auction_create_bp = Blueprint("auction_create", __name__)

# ================= CREATE AUCTION =================
@auction_create_bp.route("/auction/create", methods=["GET", "POST"])
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
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                image_urls.append(f"uploads/{filename}")

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


        db = PostgresDB()
        db.connect()
        wallet_address = db.get_wallet_address_by_user_id(seller_id)

        if not wallet_address:
            db.close()
            flash("You must have a test wallet assigned before creating an auction.", "danger")
            return redirect(url_for("auction_create.create_auction"))

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
@auction_create_bp.route("/auction/<int:auction_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("auction.detail", auction_id=auction_id))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        existing_images = raw_auction[4] if raw_auction[4] else []
        images_to_delete = request.form.getlist("delete_images")

        updated_images = [img for img in existing_images if img not in images_to_delete]

        for image_path_to_delete in images_to_delete:
            try:
                full_path = os.path.join(current_app.root_path, 'static', image_path_to_delete)
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                print(f"Error deleting file {full_path}: {e}")

        new_images = request.files.getlist("images")
        for image in new_images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
            return redirect(url_for("auction.detail", auction_id=auction_id))
        else:
            flash("Failed to update auction. Please try again.", "danger")
            return redirect(url_for("auction_create.edit_auction", auction_id=auction_id))

    auction = {
        "id": raw_auction[0],
        "title": raw_auction[2],
        "description": raw_auction[3],
        "images": raw_auction[4] if raw_auction[4] else []
    }
    db.close()
    return render_template("edit_auction.html", auction=auction)