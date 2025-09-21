module "database" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-${var.environment}-db"

  engine               = "postgres"
  engine_version       = "15.7"
  instance_class      = "db.m6g.large"
  allocated_storage   = 100
  max_allocated_storage = 1000
  storage_encrypted   = true
  kms_key_id          = aws_kms_key.rds.arn
  multi_az            = true
  db_name             = "hms_enterprise"
  username            = "hms_user"
  port                = 5432

  iam_database_authentication_enabled = true

  vpc_security_group_ids = [aws_security_group.database.id]
  maintenance_window    = "Mon:00:00-Mon:03:00"
  backup_window         = "03:00-06:00"
  backup_retention_period = var.backup_retention_days

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  create_db_parameter_group = true
  parameter_group_name = "${var.project_name}-${var.environment}-pg"
  family = "postgres15"

  parameters = [
    {
      name  = "log_connections"
      value = "1"
    },
    {
      name  = "log_disconnections"
      value = "1"
    },
    {
      name  = "log_statement"
      value = "all"
    },
    {
      name  = "log_min_duration_statement"
      value = "1000"
    },
    {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements"
    },
    {
      name  = "track_activity_query_size"
      value = "2048"
    },
    {
      name  = "max_connections"
      value = "200"
    },
    {
      name  = "shared_buffers"
      value = "{DBInstanceClassMemory/4}"
    },
    {
      name  = "effective_cache_size"
      value = "{DBInstanceClassMemory*3/4}"
    },
    {
      name  = "maintenance_work_mem"
      value = "{DBInstanceClassMemory/16}"
    },
    {
      name  = "checkpoint_completion_target"
      value = "0.9"
    },
    {
      name  = "wal_buffers"
      value = "{DBInstanceClassMemory/32}"
    },
    {
      name  = "default_statistics_target"
      value = "100"
    },
    {
      name  = "random_page_cost"
      value = "1.1"
    },
    {
      name  = "effective_io_concurrency"
      value = "200"
    },
    {
      name  = "work_mem"
      value = "{DBInstanceClassMemory/2048}"
    },
    {
      name  = "min_wal_size"
      value = "1GB"
    },
    {
      name  = "max_wal_size"
      value = "4GB"
    }
  ]

  create_db_option_group = false
  create_monitoring_role = true
  monitoring_interval    = 30
  monitoring_role_name   = "${var.project_name}-${var.environment}-rds-monitoring"
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  deletion_protection = var.environment == "production"

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }

  depends_on = [aws_security_group_database_rule]
}

resource "aws_security_group" "database" {
  name_prefix = "${var.project_name}-database"
  description = "Security group for RDS database"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
    description = "Allow EKS cluster to access database"
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Allow VPC internal access to database"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_security_group_rule" "database_rule" {
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  security_group_id = aws_security_group.database.id
  source_security_group_id = module.eks.cluster_security_group_id
}

resource "aws_db_subnet_group" "database" {
  name        = "${var.project_name}-${var.environment}-db-subnet-group"
  description = "Database subnet group for HMS"
  subnet_ids  = module.vpc.database_subnets

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_db_event_subscription" "database_events" {
  name      = "${var.project_name}-${var.environment}-db-events"
  sns_topic = aws_sns_topic.database_events.arn

  source_type = "db-instance"
  source_ids  = [module.database.db_instance_id]

  event_categories = [
    "availability",
    "deletion",
    "failover",
    "failure",
    "low storage",
    "maintenance",
    "notification",
    "recovery",
    "security",
    "configuration change"
  ]

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_sns_topic" "database_events" {
  name = "${var.project_name}-${var.environment}-db-events"

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_sns_topic_subscription" "database_email" {
  topic_arn = aws_sns_topic.database_events.arn
  protocol  = "email"
  endpoint  = "devops@${var.domain_name}"
}

resource "aws_sns_topic_subscription" "database_sms" {
  topic_arn = aws_sns_topic.database_events.arn
  protocol  = "sms"
  endpoint  = "+1234567890"
}