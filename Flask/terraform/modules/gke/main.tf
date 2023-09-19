resource "google_container_cluster" "gke-cluster" {
  name = var.name
  location = var.location

  remove_default_node_pool = true
  initial_node_count = 1
}

resource "google_container_node_pool" "gke_preemptible_nodes" {
  name = "node-pool"
  location = google_container_cluster.gke-cluster.location
  cluster = google_container_cluster.gke-cluster.name
  node_count = var.node_count
  node_locations = [ "us-south1-a" ]

  autoscaling {
    min_node_count = 1
    max_node_count = 4
  }

  node_config {
    preemptible = true
    machine_type = var.machine_type
  }
}

