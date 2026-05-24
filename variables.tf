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
