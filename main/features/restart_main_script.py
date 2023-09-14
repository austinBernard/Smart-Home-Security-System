import subprocess
import sys
from google.cloud import storage
import os

# Google Cloud Storage bucket and destination folder settings
bucket_name = 'shss-faces'
destination_folder = 'faces'

# Function to download an image from GCS
def download_image(bucket_name, source_blob_name, destination_folder):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    destination_file_path = os.path.join(destination_folder, source_blob_name)

    # Check if the image has already been downloaded
    if not os.path.exists(destination_file_path):
        blob.download_to_filename(destination_file_path)
        print(f"Downloaded {source_blob_name}")
    else:
        print(f"{source_blob_name} already exists, skipping download.")

# Function to restart the main script
def restart_main_script(channel):
    # Download images from GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        source_blob_name = blob.name
        download_image(bucket_name, source_blob_name, destination_folder)

    # Restart the main script
    subprocess.Popen(['lxterminal', '-e', 'python3', 'main.py'])
    sys.exit()

# Keep the script running
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Script terminated.")
