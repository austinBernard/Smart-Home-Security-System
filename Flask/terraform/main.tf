provider "google" {
    credentials = file("./dataapimoon-0e8296b59e2b.json")
    project = "dataapimoon"
    region = "us-south1"
    zone = "us-south1-a"
}

module "gke_cluster" {
    source = "./modules/gke"

    name = "shss-cluster"
    location = "us-south1-a"
    node_count = 2
    machine_type = "e2-small"
}