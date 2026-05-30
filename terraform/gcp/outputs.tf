output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}

output "github_actions_provider_name" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "github_actions_sa_email" {
  value = google_service_account.github_actions.email
}
