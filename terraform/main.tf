terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "your-gcp-project-id"
  region  = "us-central1"
}

# VPC Network
resource "google_compute_network" "vpc_network" {
  name                    = "collectsecure-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "default" {
  name          = "collectsecure-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = "us-central1"
  network       = google_compute_network.vpc_network.id
}

# Private Service Connect (Address for AlloyDB)
resource "google_compute_global_address" "private_ip_address" {
  name          = "collectsecure-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# AlloyDB Cluster
resource "google_alloydb_cluster" "default" {
  cluster_id = "collectsecure-cluster"
  location   = "us-central1"
  network    = google_compute_network.vpc_network.name

  initial_user {
    user     = "postgres"
    password = "change-me-securely"
  }
}

# AlloyDB Instance
resource "google_alloydb_instance" "primary" {
  cluster       = google_alloydb_cluster.default.name
  instance_id   = "collectsecure-primary-instance"
  instance_type = "PRIMARY"
}

# Cloud Cloud Storage (Letters)
resource "google_storage_bucket" "letters_bucket" {
  name     = "collectsecure-letters-bucket"
  location = "US"
  uniform_bucket_level_access = true
}

# Cloud Run Service (Backend)
resource "google_cloud_run_service" "backend" {
  name     = "collectsecure-backend"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/google-samples/hello-app:1.0" # Placeholder image
        env {
          name  = "DB_HOST"
          value = google_alloydb_instance.primary.ip_address
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Firebase Project (Frontend)
resource "google_firebase_project" "default" {
  provider = google-beta
  project  = "your-gcp-project-id"
}

resource "google_firebase_hosting_site" "default" {
  provider = google-beta
  project  = "your-gcp-project-id"
  site_id  = "collectsecure-app"
}
