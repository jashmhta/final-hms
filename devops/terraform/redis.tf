module "redis" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 1.0"

  cluster_id           = "${var.project_name}-${var.environment}-redis"
  engine               = "redis"
  engine_version       = "7.x"
  node_type            = "cache.m6g.large"
  port                 = 6379
  parameter_group_name = "default.redis7"
  security_group_ids   = [aws_security_group.redis.id]
  subnet_ids           = module.vpc.database_subnets

  replication_group_id          = "${var.project_name}-${var.environment}-redis-repl"
  automatic_failover_enabled   = true
  multi_az_enabled             = true
  at_rest_encryption_enabled   = true
  transit_encryption_enabled   = true
  auth_token                   = random_password.redis_auth_token.result
  snapshot_retention_limit     = var.backup_retention_days
  snapshot_window              = "03:00-05:00"
  maintenance_window           = "sun:05:00-sun:07:00"

  cluster_mode = {
    num_node_groups         = 2
    replicas_per_node_group = 1
  }

  apply_immediately = true

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis"
  description = "Security group for ElastiCache Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
    description = "Allow EKS cluster to access Redis"
  }

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Allow VPC internal access to Redis"
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

resource "random_password" "redis_auth_token" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_elasticache_parameter_group" "redis_custom" {
  name        = "${var.project_name}-${var.environment}-redis-params"
  family      = "redis7"
  description = "Custom Redis parameter group for HMS"

  parameter {
    name  = "cluster-enabled"
    value = "yes"
  }

  parameter {
    name  = "cluster-node-timeout"
    value = "5000"
  }

  parameter {
    name  = "cluster-announce-ip"
    value = "10.0.0.1"
  }

  parameter {
    name  = "cluster-announce-port"
    value = "6379"
  }

  parameter {
    name  = "cluster-announce-bus-port"
    value = "16379"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  parameter {
    name  = "tcp-keepalive"
    value = "60"
  }

  parameter {
    name  = "save"
    value = "900 1 300 10 60 10000"
  }

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }

  parameter {
    name  = "lua-time-limit"
    value = "5000"
  }

  parameter {
    name  = "slowlog-log-slower-than"
    value = "10000"
  }

  parameter {
    name  = "slowlog-max-len"
    value = "128"
  }

  parameter {
    name  = "hash-max-ziplist-entries"
    value = "512"
  }

  parameter {
    name  = "hash-max-ziplist-value"
    value = "64"
  }

  parameter {
    name  = "list-max-ziplist-size"
    value = "-2"
  }

  parameter {
    name  = "list-compress-depth"
    value = "0"
  }

  parameter {
    name  = "set-max-intset-entries"
    value = "512"
  }

  parameter {
    name  = "zset-max-ziplist-entries"
    value = "128"
  }

  parameter {
    name  = "zset-max-ziplist-value"
    value = "64"
  }

  parameter {
    name  = "hll-sparse-max-bytes"
    value = "3000"
  }

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-redis-cpu-high"
  alarm_description   = "Redis CPU utilization is high"
  alarm_actions       = [aws_sns_topic.redis_alerts.arn]
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  dimensions = {
    CacheClusterId = module.redis.cluster_id
  }

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${var.project_name}-${var.environment}-redis-memory-high"
  alarm_description   = "Redis memory utilization is high"
  alarm_actions       = [aws_sns_topic.redis_alerts.arn]
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 90
  comparison_operator = "GreaterThanOrEqualToThreshold"
  dimensions = {
    CacheClusterId = module.redis.cluster_id
  }

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_sns_topic" "redis_alerts" {
  name = "${var.project_name}-${var.environment}-redis-alerts"

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_sns_topic_subscription" "redis_email" {
  topic_arn = aws_sns_topic.redis_alerts.arn
  protocol  = "email"
  endpoint  = "devops@${var.domain_name}"
}