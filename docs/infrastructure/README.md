# Infrastructure as Code Documentation

This document provides comprehensive information about the Infrastructure as Code (IaC) setup for the HMS enterprise deployment.

## Overview

The HMS infrastructure is provisioned using Terraform and deployed on AWS with the following components:

- **VPC**: Isolated network environment
- **ECS**: Container orchestration
- **RDS**: Managed PostgreSQL database
- **ElastiCache**: Redis for caching and sessions
- **S3**: Object storage for backups and static files
- **CloudFront**: CDN for static assets
- **Route 53**: DNS management
- **CloudWatch**: Monitoring and logging

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │────│   Application   │
│   (CDN)         │    │   Load Balancer │
└─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
            ┌───────▼───┐ ┌───▼───┐ ┌───▼───┐
            │   ECS    │ │  RDS  │ │ Redis │
            │  Fargate │ │  PG   │ │       │
            └───────────┘ └───────┘ └───────┘
                    │
            ┌───────▼───────┐
            │     VPC       │
            │               │
            └───────────────┘
```

## Terraform Structure

### Directory Structure

```
infrastructure/
├── terraform/
│   ├── main.tf                 # Main infrastructure
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Output values
│   ├── prod.tfvars             # Production values
│   ├── modules/
│   │   ├── vpc/               # VPC module
│   │   ├── ecs/               # ECS module
│   │   ├── database/          # RDS module
│   │   └── security/          # Security groups
│   └── providers/
│       └── aws.tf             # AWS provider config
```

### Main Components

#### VPC Module

```hcl
module "vpc" {
  source = "./modules/vpc"

  name = "hms-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}
```

#### ECS Module

```hcl
module "ecs" {
  source = "./modules/ecs"

  cluster_name = "hms-cluster"

  services = {
    backend = {
      name           = "hms-backend"
      image          = var.backend_image
      cpu            = 512
      memory         = 1024
      desired_count  = 2
      container_port = 8000
    }
    frontend = {
      name           = "hms-frontend"
      image          = var.frontend_image
      cpu            = 256
      memory         = 512
      desired_count  = 2
      container_port = 80
    }
  }
}
```

#### Database Module

```hcl
module "database" {
  source = "./modules/database"

  identifier = "hms-db"

  engine         = "postgres"
  engine_version = "16.0"
  instance_class = "db.t3.medium"

  allocated_storage = 100
  storage_encrypted = true

  db_name  = "hms"
  username = var.db_username
  password = var.db_password
  port     = 5432

  vpc_security_group_ids = [module.security.database_sg_id]
  subnet_ids             = module.vpc.private_subnets

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
}
```

## Deployment Process

### 1. Prerequisites

```bash
# Install Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com jammy main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Configure AWS CLI
aws configure
```

### 2. Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### 3. Plan Deployment

```bash
terraform plan -var-file=prod.tfvars
```

### 4. Apply Changes

```bash
terraform apply -var-file=prod.tfvars
```

### 5. Verify Deployment

```bash
# Check ECS services
aws ecs list-services --cluster hms-cluster

# Check RDS instance
aws rds describe-db-instances --db-instance-identifier hms-db

# Check load balancer
aws elbv2 describe-load-balancers
```

## Configuration Management

### Environment Variables

```hcl
# variables.tf
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
```

### Production Values

```hcl
# prod.tfvars
environment = "production"

db_username = "hms_prod"
db_password = "strong-production-password-2024"

backend_image  = "123456789012.dkr.ecr.us-east-1.amazonaws.com/hms-backend:v1.2.0"
frontend_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/hms-frontend:v1.2.0"

domain_name = "hms.yourcompany.com"
```

## Security Configuration

### Security Groups

```hcl
# modules/security/main.tf
resource "aws_security_group" "alb" {
  name_prefix = "hms-alb-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs" {
  name_prefix = "hms-ecs-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "database" {
  name_prefix = "hms-db-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### IAM Roles and Policies

```hcl
# ECS Task Execution Role
resource "aws_iam_role" "ecs_execution" {
  name = "hms-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
```

## Monitoring and Logging

### CloudWatch Configuration

```hcl
# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/hms"
  retention_in_days = 30
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "cpu_utilization" {
  alarm_name          = "hms-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ecs cpu utilization"
}
```

### X-Ray Integration

```hcl
# X-Ray configuration for tracing
resource "aws_xray_sampling_rule" "hms" {
  rule_name      = "hms-sampling"
  priority       = 100
  reservoir_size = 1
  fixed_rate     = 0.05
  service_type   = "*"
  service_name   = "*"
  http_method    = "*"
  url_path       = "*"
}
```

## Backup and Recovery

### RDS Backup Configuration

```hcl
resource "aws_db_instance" "hms" {
  # ... other configuration

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # Enable automated backups
  backup_retention_period = 7

  # Enable encryption
  storage_encrypted = true
  kms_key_id       = aws_kms_key.rds.arn
}
```

### S3 Backup Bucket

```hcl
resource "aws_s3_bucket" "backups" {
  bucket = "hms-backups-${var.environment}"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "backup_retention"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}
```

## Cost Optimization

### Auto Scaling

```hcl
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.hms.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

### Reserved Instances

```hcl
resource "aws_rds_reserved_instance" "hms_db" {
  instance_class    = "db.t3.medium"
  instance_count    = 1
  offering_type     = "Partial Upfront"
  product_description = "postgresql"
  reservation_id    = "hms-db-reservation"
}
```

## Troubleshooting

### Common Issues

1. **Terraform State Lock**
   ```bash
   # Force unlock (use with caution)
   terraform force-unlock LOCK_ID
   ```

2. **ECS Service Deployment Failures**
   ```bash
   # Check service events
   aws ecs describe-services --cluster hms-cluster --services hms-backend

   # Check task definition
   aws ecs describe-task-definition --task-definition hms-backend
   ```

3. **Database Connection Issues**
   ```bash
   # Check security groups
   aws ec2 describe-security-groups --group-ids sg-xxxxx

   # Test database connectivity
   aws rds describe-db-instances --db-instance-identifier hms-db
   ```

### Debugging Commands

```bash
# List all resources
terraform state list

# Show resource details
terraform state show aws_ecs_service.backend

# Import existing resources
terraform import aws_db_instance.hms hms-db

# Destroy specific resources
terraform destroy -target=aws_ecs_service.backend
```

## Best Practices

### Code Organization

1. **Modular Structure**: Use modules for reusable components
2. **Variable Validation**: Validate input variables
3. **Output Documentation**: Document all outputs
4. **State Management**: Use remote state with locking

### Security

1. **Least Privilege**: Grant minimal required permissions
2. **Encryption**: Encrypt data at rest and in transit
3. **Network Isolation**: Use private subnets for sensitive resources
4. **Access Control**: Implement proper IAM policies

### Performance

1. **Resource Sizing**: Right-size instances based on load
2. **Caching**: Implement Redis for session and data caching
3. **CDN**: Use CloudFront for static asset delivery
4. **Auto Scaling**: Configure automatic scaling based on metrics

### Monitoring

1. **Comprehensive Logging**: Enable detailed logging
2. **Metric Collection**: Monitor key performance indicators
3. **Alerting**: Set up alerts for critical issues
4. **Dashboard**: Create operational dashboards

## Support

For infrastructure support:
- Check Terraform documentation: https://registry.terraform.io/
- AWS documentation: https://docs.aws.amazon.com/
- Contact DevOps team for custom configurations
