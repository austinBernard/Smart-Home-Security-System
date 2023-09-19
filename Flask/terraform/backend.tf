terraform {
  backend "gcs" {
    bucket = "tf-backend-shss"
    prefix = "terraform/state"
    credentials = "./dataapimoon-0e8296b59e2b.json"
  }
}