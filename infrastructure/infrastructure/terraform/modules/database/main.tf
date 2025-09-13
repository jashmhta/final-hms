resource "aws_security_group" "database" {
  name_prefix = "hms-db-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.private_subnet_cidr
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name  = "hms-database-sg"
    HIPAA = "true"
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "hms-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name  = "hms-db-subnet-group"
    HIPAA = "true"
  }
}

resource "aws_db_instance" "main" {
  identifier              = "hms-${var.environment}-db"
  engine                 = "postgres"
  engine_version         = "13.7"
  instance_class         = var.instance_class
  allocated_storage      = 100
  max_allocated_storage  = 1000
  storage_type           = "gp3"
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.db.arn  # HIPAA: Customer-managed KMS key

  db_name  = "hmsdb"
  username = var.username
  password = var.password

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"

  multi_az               = true  # HIPAA: High availability
  publicly_accessible    = false

  monitoring_interval    = 60
  monitoring_role_arn    = aws_iam_role.enhanced_monitoring.arn

  # HIPAA: Enable deletion protection and audit logging
  deletion_protection    = var.environment == "prod" ? true : false
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  parameter_group_name = aws_db_parameter_group.main.name

  tags = {
    Name  = "hms-${var.environment}-database"
    HIPAA = "true"
  }
}

# KMS Key for database encryption (HIPAA requirement)
resource "aws_kms_key" "db" {
  description             = "KMS key for HMS database encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = { AWS = "*" }
        Action = "kms:*"
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "rds.${data.aws_region.current.name}.amazonaws.com"
          }
        }
      },
      {
        Effect = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/hms-rds-role" }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name  = "hms-db-kms-key"
    HIPAA = "true"
  }
}

resource "aws_kms_alias" "db" {
  name          = "alias/hms-db-key"
  target_key_id = aws_kms_key.db.key_id
}

# Enhanced monitoring role
resource "aws_iam_role" "enhanced_monitoring" {
  name = "hms-rds-enhanced-monitoring-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "enhanced_monitoring" {
  role       = aws_iam_role.enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Database parameter group for HIPAA compliance
resource "aws_db_parameter_group" "main" {
  name   = "hms-${var.environment}-params"
  family = "postgres13"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "rds.log_retention_period"
    value = "1440"
  }

  tags = {
    Name  = "hms-${var.environment}-db-params"
    HIPAA = "true"
  }
}

# Data sources
data "aws_region" "current" {}

data "aws_caller_identity" "current" {}
