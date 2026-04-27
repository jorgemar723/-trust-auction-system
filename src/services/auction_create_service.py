import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from db.repository_factory import get_user_repository, get_auction_repository
from backend.mainauction import create_new_auction as deploy_auction
from app.utils.datetime_utils import parse_local_datetime_to_utc
from app.utils.s3_utils import upload_file_to_s3, delete_file_from_s3

class AuctionCreateService:
    @staticmethod
    def create_auction(user_id, title, description, starting_bid, expires_at, images):
        bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")
        if not bucket_name:
            return {"success": False, "message": "", "error": "Server configuration error: S3 bucket is not configured."}

        image_urls = []
        for image in images:
            if image and image.filename:
                image_url = upload_file_to_s3(image, bucket_name)
                if image_url:
                    image_urls.append(image_url)
                else:
                    return {"success": False, "message": "", "error": f"Failed to upload image: {secure_filename(image.filename)}"}

        created_at = datetime.now(timezone.utc)
        
        try:
            expires_at_utc = parse_local_datetime_to_utc(expires_at)
        except Exception:
            return {"success": False, "message": "", "error": "Invalid date format."}

        result_seconds = int(expires_at_utc.timestamp()) - int(created_at.timestamp())

        if result_seconds <= 0:
            return {"success": False, "message": "", "error": "Invalid auction time. Please select a future time."}

        if starting_bid <= 0:
            return {"success": False, "message": "", "error": "Starting bid must be a positive value."}

        user_repo = get_user_repository()
        auction_repo = get_auction_repository()
        try:
            wallet_address = user_repo.get_wallet_address_by_user_id(user_id)
            if not wallet_address:
                return {"success": False, "message": "", "error": "You must have a test wallet assigned before creating an auction."}

            try:
                result = deploy_auction(result_seconds, wallet_address, starting_bid)
                contract_address = result["auction_address"]
                tx_hash = result["tx_hash"]
            except Exception as e:
                return {"success": False, "message": "", "error": f"Failed to deploy auction contract: {str(e)}"}

            success = auction_repo.create_auction(
                title=title,
                description=description,
                starting_bid=starting_bid,
                image_urls=image_urls,
                created_at=created_at,
                expires_at=expires_at_utc,
                seller_id=user_id,
                contract_address=contract_address,
                tx_hash=tx_hash
            )

            if success:
                return {"success": True, "message": "Auction created successfully.", "error": ""}
            else:
                return {"success": False, "message": "", "error": "Failed to create auction in database. Please try again."}
            
        except Exception as e:
            print(f"Error creating auction: {e}")
            return {"success": False, "message": "", "error": "An unexpected error occurred while creating the auction."}

    @staticmethod
    def get_auction_for_edit(auction_id, user_id):
        auction_repo = get_auction_repository()
        try:
            raw_auction = auction_repo.get_auction_by_id(auction_id)
            if not raw_auction:
                return {"success": False, "message": "", "error": "Auction not found."}

            seller_id = raw_auction[1]
            if user_id != seller_id:
                return {"success": False, "message": "", "error": "You are not authorized to edit this auction.", "unauthorized": True}

            auction = {
                "id": raw_auction[0],
                "title": raw_auction[2],
                "description": raw_auction[3],
                "images": raw_auction[4] if raw_auction[4] else []
            }
            return {"success": True, "message": "Auction fetched successfully.", "error": "", "auction": auction}
        except Exception as e:
            print(f"Error fetching auction for edit: {e}")
            return {"success": False, "message": "", "error": "An unexpected error occurred while fetching the auction."}

    @staticmethod
    def edit_auction(auction_id, user_id, title, description, images_to_delete, new_images):
        auction_repo = get_auction_repository()
        try:
            raw_auction = auction_repo.get_auction_by_id(auction_id)
            if not raw_auction:
                return {"success": False, "message": "", "error": "Auction not found."}

            seller_id = raw_auction[1]
            if user_id != seller_id:
                return {"success": False, "message": "", "error": "You are not authorized to edit this auction."}

            existing_images = raw_auction[4] if raw_auction[4] else []
            bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")

            if not bucket_name:
                return {"success": False, "message": "", "error": "Server configuration error: S3 bucket not configured."}

            # Handle image deletions
            updated_images = [img for img in existing_images if img not in images_to_delete]
            for url_to_delete in images_to_delete:
                delete_file_from_s3(url_to_delete, bucket_name)

            # Handle new image uploads
            for image in new_images:
                if image and image.filename:
                    image_url = upload_file_to_s3(image, bucket_name)
                    if image_url:
                        updated_images.append(image_url)
                    else:
                        return {"success": False, "message": "", "error": f"Failed to upload new image: {secure_filename(image.filename)}"}

            success = auction_repo.update_auction(
                auction_id=auction_id,
                title=title,
                description=description,
                image_urls=updated_images
            )

            if success:
                return {"success": True, "message": "Auction updated successfully.", "error": ""}
            else:
                return {"success": False, "message": "", "error": "Failed to update auction. Please try again."}
        except Exception as e:
            print(f"Error editing auction: {e}")
            return {"success": False, "message": "", "error": "An unexpected error occurred while editing the auction."}