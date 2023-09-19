# Builds the docker image with the Dockerfile
docker build -t us.gcr.io/dataapimoon/my-flask-app:1.0 .


# Pushes the image to the GCR
docker push us.gcr.io/dataapimoon/my-flask-app:1.0


# Preqreuiments before deploying
gcloud components install kubectl
gcloud components install gke-gcloud-auth-plugin


# Deploying to GKE cluster
gcloud container clusters get-credentials shss-cluster --zone us-south1-a
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

kubectl create deployment my-flask-server --image=us.gcr.io/dataapimoon/my-flask-app:1.0
kubectl expose deployment my-flask-server --type LoadBalancer --port 80 --target-port 8080 
gcloud projects add-iam-policy-binding dataapimoon --member serviceAccount:docker-sa@dataapimoon.iam.gserviceaccount.com --role roles/storage.objectCreator


# Creating clusters
gcloud container clusters create shss-cluster


# Troubleshoot (my-flask-app-6bbcf5688d-ffrf7 -> pod name)
kubectl logs -n default my-flask-app-6bbcf5688d-ffrf7


# For local testing on Docker
docker run -e GOOGLE_APPLICATION_CREDENTIALS=dataapimoon-0e8296b59e2b.json -v /dataapimoon-0e8296b59e2b.json -p 8080:8080 us.gcr.io/dataapimoon/my-flask-app:1.0