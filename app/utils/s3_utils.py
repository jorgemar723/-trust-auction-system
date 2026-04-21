import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError
from werkzeug.utils import secure_filename

def get_s3_client():
    """Initializes and returns a boto3 S3 client."""
    # Boto3 will automatically look for credentials in environment variables
    # (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or an attached IAM role.
    return boto3.client(
        "s3",
        region_name=os.environ.get("AWS_S3_REGION")
    )

def upload_file_to_s3(file, bucket_name, acl="public-read"):
    """
    Uploads a file to an S3 bucket.

    :param file: File to upload (from request.files)
    :param bucket_name: Bucket to upload to
    :param acl: Access control list for the uploaded file
    :return: The public URL of the file, or None if upload fails
    """
    s3_client = get_s3_client()
    filename = secure_filename(file.filename)

    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )
    except NoCredentialsError:
        print("Error: AWS credentials not found.")
        return None
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return None

    # Construct the public URL
    region = os.environ.get("AWS_S3_REGION")
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{filename}"

def delete_file_from_s3(file_url, bucket_name):
    """
    Deletes a file from an S3 bucket based on its URL.

    :param file_url: The public URL of the file to delete.
    :param bucket_name: The S3 bucket name.
    :return: True if deletion was successful, False otherwise.
    """
    if not file_url or not bucket_name:
        return False
        
    s3_client = get_s3_client()
    # Extract object key from URL.
    # e.g., https://my-bucket.s3.us-east-1.amazonaws.com/my-image.jpg -> my-image.jpg
    try:
        key = file_url.split(f".s3.amazonaws.com/")[1]
        s3_client.delete_object(Bucket=bucket_name, Key=key)
    except (ClientError, IndexError, NoCredentialsError) as e:
        print(f"Error deleting file from S3: {e}")
        return False
    return True