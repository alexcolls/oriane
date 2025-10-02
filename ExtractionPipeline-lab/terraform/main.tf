resource "aws_iam_role" "batch_task" {
  name = "batch-gpu-task"
  assume_role_policy = data.aws_iam_policy_document.batch_assume.json
}
# inline policies: s3 read/write + Database secret (ssm:GetParameter) …

resource "aws_batch_compute_environment" "gpu" {
  compute_environment_name = "gpu-prod"
  compute_resources {
    type              = "EC2"
    instance_role     = "ecsInstanceRole"
    instance_types    = ["g5.xlarge","g4dn.xlarge"]
    min_vcpus         = 0
    max_vcpus         = 256        # ✱ scale-out limit
    subnets           = var.private_subnets
    security_group_ids= [aws_security_group.batch.id]
  }
  service_role = aws_iam_role.batch_service.arn
  type         = "MANAGED"
}
resource "aws_batch_job_queue" "main" {
  name                 = "gpu-queue"
  state                = "ENABLED"
  priority             = 1
  compute_environments = [aws_batch_compute_environment.gpu.arn]
}

resource "aws_batch_job_definition" "extract" {
  name       = "extract-frames"
  type       = "container"
  platform_capabilities = ["EC2"]
  container_properties = jsonencode({
    image      = "${aws_ecr_repository.pipeline.repository_url}:latest"
    vcpus      = 4
    memory     = 15000          # MB
    resourceRequirements = [{type="GPU",value="1"}]
    environment = [
      { name="AWS_REGION" , value=var.aws_region },
      { name="S3_VIDEOS_BUCKET"  , value=var.s3_bucket },
      { name="S3_FRAMES_BUCKET"  , value=var.s3_bucket_frames },
      { name="DB_HOST" , value=aws_ssm_parameter.db_host.value },
      { name="DB_PORT" , value=aws_ssm_parameter.db_port.value },
      { name="DB_USER" , value=aws_ssm_parameter.db_user.value },
      { name="DB_PASSWORD" , value=aws_ssm_parameter.db_password.value },
      { name="DB_NAME" , value=aws_ssm_parameter.db_name.value }
    ]
  })
}
