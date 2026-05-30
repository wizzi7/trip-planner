resource "null_resource" "seed_ecr_backend" {
  depends_on = [aws_ecr_repository.backend]
  provisioner "local-exec" {
    command = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.backend.repository_url} && docker build -t ${aws_ecr_repository.backend.repository_url}:latest -f Dockerfile.backend.seed . && docker push ${aws_ecr_repository.backend.repository_url}:latest"
    interpreter = ["cmd", "/C"]
  }
}

resource "null_resource" "seed_ecr_frontend" {
  depends_on = [aws_ecr_repository.frontend]
  provisioner "local-exec" {
    command = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.frontend.repository_url} && docker build -t ${aws_ecr_repository.frontend.repository_url}:latest -f Dockerfile.frontend.seed . && docker push ${aws_ecr_repository.frontend.repository_url}:latest"
    interpreter = ["cmd", "/C"]
  }
}
