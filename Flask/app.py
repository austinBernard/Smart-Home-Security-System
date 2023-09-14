import os
from flask import Flask, request, render_template
from google.cloud import storage

# Set the path to the service account credentials JSON file
credentials_path = 'dataapimoon-0e8296b59e2b.json'

# Explicitly create the storage client with the credentials file path
storage_client = storage.Client.from_service_account_json(credentials_path)

app = Flask(__name__, template_folder='templates')

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
            blob.upload_from_string(uploaded_file.read(), content_type=uploaded_file.content_type)

            return 'File uploaded successfully!'

    return render_template('upload.html')

if __name__ == '__main__':
    print(f"Where=  {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
    app.run(host='0.0.0.0', port=8080)
