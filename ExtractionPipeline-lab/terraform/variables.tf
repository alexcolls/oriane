variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "private_subnets" {
  description = "List of private subnet IDs for Batch compute environment"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID where resources will be provisioned"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block of the VPC (used for SG rules)"
  type        = string
}

variable "s3_bucket" {
  description = "S3 bucket storing input videos"
  type        = string
}

variable "s3_bucket_frames" {
  description = "S3 bucket storing extracted frames"
  type        = string
}

# ─── Database connection details (stored in SSM) ──────────────────
variable "db_host_value" {
  description = "Aurora PostgreSQL host"
  type        = string
  sensitive   = true
}

variable "db_port_value" {
  description = "Aurora PostgreSQL port"
  type        = string
  sensitive   = true
  default     = "5432"
}

variable "db_user_value" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password_value" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_name_value" {
  description = "Database name"
  type        = string
  default     = "oriane_db"
} 