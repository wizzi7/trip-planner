output "ecr_repository_backend" {
  value = aws_ecr_repository.backend.repository_url
}

output "ecr_repository_frontend" {
  value = aws_ecr_repository.frontend.repository_url
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}

output "frontend_url" {
  value       = "http://${aws_lb.frontend.dns_name}"
  description = "The public URL of the trip planner frontend (ALB)"
}
