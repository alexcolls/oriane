# ──────────────────────────────────────────────
# SSM Parameter Store – database connection secrets
# ──────────────────────────────────────────────

resource "aws_ssm_parameter" "db_host" {
  name  = "/oriane/db/host"
  type  = "String"
  value = var.db_host_value
}

resource "aws_ssm_parameter" "db_port" {
  name  = "/oriane/db/port"
  type  = "String"
  value = var.db_port_value
}

resource "aws_ssm_parameter" "db_user" {
  name  = "/oriane/db/user"
  type  = "String"
  value = var.db_user_value
}

resource "aws_ssm_parameter" "db_password" {
  name      = "/oriane/db/password"
  type      = "SecureString"
  value     = var.db_password_value
  overwrite = true
}

resource "aws_ssm_parameter" "db_name" {
  name  = "/oriane/db/name"
  type  = "String"
  value = var.db_name_value
} 