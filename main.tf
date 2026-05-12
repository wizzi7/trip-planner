terraform {
  backend "gcs" {
    bucket = "trip-planner-tfstate"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Zmienne ───────────────────────────────────────────────────────────────────

variable "project_id" {
  default = "trip-planner-prd"
}

variable "region" {
  default = "europe-central2"
}

variable "google_api_key" {
  sensitive = true
}

variable "openai_api_key" {
  sensitive = true
}

variable "anthropic_api_key" {
  sensitive = true
}

# ── Lokalny skrót do ścieżki repozytorium ────────────────────────────────────

locals {
  repo = "${var.region}-docker.pkg.dev/${var.project_id}/trip-planner"
}

# ── Włączenie wymaganych API ──────────────────────────────────────────────────

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "compute.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# ── Sieć (VPC) i NAT ──────────────────────────────────────────────────────────

resource "google_compute_network" "vpc" {
  name                    = "trip-planner-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "subnet" {
  name                     = "trip-planner-subnet"
  ip_cidr_range            = "10.0.0.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
}

resource "google_compute_router" "router" {
  name    = "trip-planner-router"
  network = google_compute_network.vpc.name
  region  = var.region
}

resource "google_compute_router_nat" "nat" {
  name                               = "trip-planner-nat"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# ── Artifact Registry ─────────────────────────────────────────────────────────

resource "google_artifact_registry_repository" "trip_planner" {
  repository_id = "trip-planner"
  format        = "DOCKER"
  location      = var.region
  description   = "Trip Planner container images"

  depends_on = [google_project_service.apis]
}

# ── Secret Manager ────────────────────────────────────────────────────────────

resource "google_secret_manager_secret" "google_api_key" {
  secret_id = "google-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "google_api_key" {
  secret      = google_secret_manager_secret.google_api_key.id
  secret_data = var.google_api_key
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "anthropic_api_key" {
  secret      = google_secret_manager_secret.anthropic_api_key.id
  secret_data = var.anthropic_api_key
}

# ── Service Accounts ──────────────────────────────────────────────────────────

resource "google_service_account" "backend_sa" {
  account_id   = "backend-sa"
  display_name = "Backend Service Account"
}

resource "google_service_account" "frontend_sa" {
  account_id   = "frontend-sa"
  display_name = "Frontend Service Account"
}

resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# ── Cloud Run: Backend ────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "backend" {
  name     = "trip-planner-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.backend_sa.email

    scaling {
      min_instance_count = 0 # scale-to-zero w okresach bezczynności
      max_instance_count = 3
    }

    timeout = "600s"

    max_instance_request_concurrency = 10

    containers {
      image = "${local.repo}/backend:latest"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          memory = "1Gi"
          cpu    = "1"
        }
      }

      # Sekrety wstrzykiwane jako zmienne środowiskowe
      dynamic "env" {
        for_each = {
          GOOGLE_API_KEY    = google_secret_manager_secret.google_api_key.secret_id
          OPENAI_API_KEY    = google_secret_manager_secret.openai_api_key.secret_id
          ANTHROPIC_API_KEY = google_secret_manager_secret.anthropic_api_key.secret_id
        }
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [
    google_project_iam_member.secret_accessor,
    google_artifact_registry_repository.trip_planner,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Cloud Run: Frontend ───────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "frontend" {
  name     = "trip-planner-frontend"
  location = var.region

  template {
    service_account = google_service_account.frontend_sa.email

    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.id
        subnetwork = google_compute_subnetwork.subnet.id
      }
      egress = "ALL_TRAFFIC"
    }

    scaling {
      min_instance_count = 1 # always-on — Streamlit przechowuje session_state w pamięci
      max_instance_count = 2
    }

    containers {
      image = "${local.repo}/frontend:latest"

      ports {
        container_port = 8501
      }

      resources {
        limits = {
          memory = "512Mi"
          cpu    = "1"
        }
      }

      env {
        name  = "API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }

  depends_on = [
    google_cloud_run_v2_service.backend,
    google_artifact_registry_repository.trip_planner,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Outputy ───────────────────────────────────────────────────────────────────

output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}
