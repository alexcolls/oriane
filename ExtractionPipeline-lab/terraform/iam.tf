# ──────────────────────────────────────────────
# IAM roles & policies for AWS Batch
# ──────────────────────────────────────────────

# Trust policy for Batch task containers (ECS tasks)
# NOTE: aws_iam_role.batch_task is declared in main.tf – attach inline policies here

data "aws_iam_policy_document" "batch_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# Trust policy for AWS Batch service role

data "aws_iam_policy_document" "batch_service_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["batch.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# ─── Batch service role (managed policy) ───────────────────────────
resource "aws_iam_role" "batch_service" {
  name               = "batch-service-role"
  assume_role_policy = data.aws_iam_policy_document.batch_service_assume.json
}

resource "aws_iam_role_policy_attachment" "batch_service_managed" {
  role       = aws_iam_role.batch_service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

# ─── Batch task role inline policy (S3 + SSM read) ────────────────
data "aws_iam_policy_document" "batch_task_inline" {
  statement {
    sid    = "S3Access"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.s3_bucket}",
      "arn:aws:s3:::${var.s3_bucket}/*",
      "arn:aws:s3:::${var.s3_bucket_frames}",
      "arn:aws:s3:::${var.s3_bucket_frames}/*"
    ]
  }

  statement {
    sid       = "SSMRead"
    effect    = "Allow"
    actions   = ["ssm:GetParameter", "ssm:GetParameters"]
    resources = [
      aws_ssm_parameter.db_host.arn,
      aws_ssm_parameter.db_port.arn,
      aws_ssm_parameter.db_user.arn,
      aws_ssm_parameter.db_password.arn,
      aws_ssm_parameter.db_name.arn
    ]
  }
}

resource "aws_iam_role_policy" "batch_task_inline" {
  name   = "batch-task-inline"
  role   = aws_iam_role.batch_task.id
  policy = data.aws_iam_policy_document.batch_task_inline.json
} 