resource "aws_security_group" "batch" {
  name        = "batch-sg"
  description = "Security group for AWS Batch compute resources"
  vpc_id      = var.vpc_id

  # Allow all traffic within VPC
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr_block]
  }

  # Allow outbound internet
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "batch-sg"
  }
} 