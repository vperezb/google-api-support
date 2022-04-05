import functools
import mimetypes
import datetime

from google.cloud import storage


@functools.lru_cache()
def get_storage_client():
    return storage.Client()


def upload_from_filename_to_google_storage(filename, bucketName,
        destination_blob_name):
    """Uploads a file from a filename to the bucket. 
    The permisions will be inherited from the bucket"""
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(destination_blob_name)
    content_type = mimetypes.guess_type(filename)[0]
    if content_type:
        blob.content_type = content_type
    blob.upload_from_filename(filename)
    return blob.public_url


def get_signed_URL(bucketname, filename, action="GET"):
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucketname)
    blob = bucket.blob(filename)
    url = blob.generate_signed_url(
        expiration=datetime.timedelta(minutes=30),
        method=action, version="v4")
    return url