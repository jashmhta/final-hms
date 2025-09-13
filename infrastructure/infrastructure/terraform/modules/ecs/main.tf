resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"  # HIPAA: Enhanced monitoring
  }

  tags = {
    Name  = "hms-${var.environment}-cluster"
    HIPAA = "true"
  }
}

resource "aws_ecs_task_definition" "hms_service" {
  for_each          = toset(var.services)
  family            = "hms-${each.key}"
  network_mode      = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu               = "256"
  memory            = "512"
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn     = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "hms-${each.key}"
      image = "hms/${each.key}:latest"
      essential = true
      portMappings = [{
        containerPort = 8000
        protocol      = "tcp"
      }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
          "awslogs-datetime-format" = ".%Y-%m-%dT%H:%M:%S%z"
        }
      }
      environment = [
        {
          name  = "DB_HOST"
          value = var.db_endpoint
        },
        {
          name  = "DB_PORT"
          value = tostring(var.db_port)
        },
        {
          name  = "DB_USER"
          value = var.db_username
        },
        {
          name  = "DB_PASSWORD"
          value = var.db_password
        }
      ]
      healthCheck = {
        command = ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1"]
        interval = 30
        timeout  = 5
        retries  = 3
        startPeriod = 10
      }
    }
  ])

  tags = {
    Name  = "hms-${each.key}-task"
    HIPAA = "true"
  }
}

resource "aws_ecs_service" "hms_service" {
  for_each = toset(var.services)

  name            = "hms-${each.key}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.hms_service[each.key].arn
  desired_count   = 2  # Multi-AZ for 99.99% uptime

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main[each.key].arn
    container_name   = "hms-${each.key}"
    container_port   = 8000
  }

  health_check_grace_period_seconds = 60

  # Blue/Green deployment for zero-downtime
  deployment_controller {
    type = "CODE_DEPLOY"
  }

  tags = {
    Name  = "hms-${each.key}-service"
    HIPAA = "true"
  }
  depends_on = [aws_lb_listener.http]
}

# IAM Roles for ECS
resource "aws_iam_role" "ecs_execution" {
  name = "hms-ecs-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name = "hms-ecs-task-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "hms-ecs-task-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "secretsmanager:GetSecretValue"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/hms-${var.environment}"
  retention_in_days = 365  # HIPAA requirement

  tags = {
    Name  = "hms-ecs-logs"
    HIPAA = "true"
  }
}

# ALB for services
resource "aws_lb" "main" {
  name               = "hms-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod"

  tags = {
    Name  = "hms-alb"
    HIPAA = "true"
  }
}

resource "aws_lb_target_group" "main" {
  for_each = toset(var.services)

  name     = "hms-${each.key}-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  tags = {
    Name  = "hms-${each.key}-target-group"
    HIPAA = "true"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main[var.services[0]].arn  # Default to first service
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "hms-alb-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name  = "hms-alb-sg"
    HIPAA = "true"
  }
}

resource "aws_security_group" "ecs_tasks" {
  name_prefix = "hms-ecs-tasks-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name  = "hms-ecs-tasks-sg"
    HIPAA = "true"
  }
}

# Data sources
data "aws_region" "current" {}
