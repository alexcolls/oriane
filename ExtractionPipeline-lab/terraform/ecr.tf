# ──────────────────────────────────────────────
# Amazon ECR repositories for container images
# ──────────────────────────────────────────────

resource "aws_ecr_repository" "pipeline" {
  name = "extraction-pipeline-image-py"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = "OrianeExtraction"
    Component = "Pipeline"
  }
}

resource "aws_ecr_repository" "api" {
  name = "extraction-pipeline-api"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = "OrianeExtraction"
    Component = "API"
  }
} 