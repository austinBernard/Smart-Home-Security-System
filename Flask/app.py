import os
from flask import Flask, request, render_template, Response
from google.cloud import storage
from datetime import datetime, timedelta

# Set the path to the service account credentials JSON file
credentials_path = 'dataapimoon-0e8296b59e2b.json'

# Explicitly create the storage client with the credentials file path
storage_client = storage.Client.from_service_account_json(credentials_path)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Replace with your GCS bucket name
BUCKET_NAME = 'shss-faces'

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        uploaded_file = request.files['file']

        if uploaded_file:
            # Upload the file to GCS
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(uploaded_file.filename)
            
            if blob.exists():
                return 'File already exists!'
            
            blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.content_type)

            return 'File uploaded successfully!'

    return render_template('upload.html')

def convert_utc_to_timezone(utc_time, timezone):
    return utc_time + timedelta(hours=timezone)

@app.route('/image-list')
def list_images():
    # Specify the GCS bucket where your images are stored
    bucket = storage_client.bucket(BUCKET_NAME)

    # List all blobs (images) in the bucket
    blobs = bucket.list_blobs()

    # Create a list to store image information including filename and upload time
    image_info = []
    image_groups = {}

    # Define the desired time zone offset in hours (e.g., -5 for Eastern Time)
    desired_timezone_offset = -5

    # Iterate through the blobs and add image info to the list
    for blob in blobs:
        filename = blob.name
        upload_time_utc = blob.time_created  # Timestamp in UTC
        upload_time = convert_utc_to_timezone(upload_time_utc, desired_timezone_offset)  # Convert to desired time zone
        formatted_time = upload_time.strftime('%Y-%m-%d %I:%M %p')  # Format the time in 12-hour format
        image_info.append((filename, formatted_time))  # Append formatted time
        
        upload_time = blob.time_created
        upload_date = upload_time.strftime('%Y-%m-%d')  # Extract the date in YYYY-MM-DD format

        # Check if the upload_date is already a key in the dictionary
        if upload_date not in image_groups:
            image_groups[upload_date] = []

        # Append the filename to the corresponding date's list
        image_groups[upload_date].append(filename)
        
        

    # Sort the image_info list in descending order by upload_time
    image_info = sorted(image_info, key=lambda x: x[1], reverse=True)

    # Extract filenames from sorted image_info
    sorted_filenames = [info[0] for info in image_info]
    sorted_dates = sorted(image_groups.keys(), reverse=True)
    for date in image_groups:
        image_groups[date] = sorted(image_groups[date], key=lambda x: x[1], reverse=True)

    # Render the HTML template and pass the sorted_filenames to it
    return render_template('list_images.html', filenames=sorted_filenames, image_groups=image_groups, image_info=image_info, sorted_dates=sorted_dates)

@app.route('/images/<filename>')
def serve_image(filename):
    # Specify the GCS bucket where your images are stored
    bucket = storage_client.bucket(BUCKET_NAME)

    # Check if the requested image exists in the bucket
    blob = bucket.blob(filename)
    if not blob.exists():
        return 'Image not found', 404

    # Set the content type header based on the image file type
    content_type = 'image/jpeg'  # Change this based on your image types
    if filename.endswith('.png'):
        content_type = 'image/png'
    elif filename.endswith('.gif'):
        content_type = 'image/gif'

    # Fetch the image data from GCS and serve it with the correct content type
    image_data = blob.download_as_bytes()
    return Response(image_data, content_type=content_type)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
