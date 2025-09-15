# Enterprise IAM Policies for HMS Security

# Super Admin Policy
resource "aws_iam_policy" "super_admin_policy" {
  name        = "hms-super-admin-policy"
  description = "Full access policy for HMS super administrators"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:*",
          "rds:*",
          "s3:*",
          "kms:*",
          "secretsmanager:*",
          "cloudwatch:*",
          "logs:*",
          "iam:*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = var.allowed_regions
          }
        }
      }
    ]
  })
}

# Hospital Admin Policy
resource "aws_iam_policy" "hospital_admin_policy" {
  name        = "hms-hospital-admin-policy"
  description = "Hospital-level administrative access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::hms-${var.environment}-hospital-*",
          "arn:aws:s3:::hms-${var.environment}-hospital-*/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ]
        Resource = "arn:aws:rds:${var.region}:${var.account_id}:db:hms-${var.environment}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.region}:${var.account_id}:log-group:/hms/${var.environment}/*"
      }
    ]
  })
}

# Read-Only Policy
resource "aws_iam_policy" "read_only_policy" {
  name        = "hms-read-only-policy"
  description = "Read-only access for auditors and support staff"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "rds:Describe*",
          "s3:GetObject",
          "s3:ListBucket",
          "cloudwatch:Get*",
          "cloudwatch:List*",
          "logs:Describe*",
          "logs:Get*",
          "logs:FilterLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Deny"
        Action = [
          "ec2:Modify*",
          "rds:Modify*",
          "s3:PutObject",
          "s3:DeleteObject",
          "logs:Delete*",
          "logs:CreateLogGroup"
        ]
        Resource = "*"
      }
    ]
  })
}

# Database Access Policy
resource "aws_iam_policy" "database_access_policy" {
  name        = "hms-database-access-policy"
  description = "Controlled database access with encryption requirements"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:Connect"
        ]
        Resource = "arn:aws:rds-db:${var.region}:${var.account_id}:dbuser:*/hms_app_user"
        Condition = {
          Bool = {
            "aws:SecureTransport" = "true"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "arn:aws:kms:${var.region}:${var.account_id}:key/*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "rds.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Security Audit Policy
resource "aws_iam_policy" "security_audit_policy" {
  name        = "hms-security-audit-policy"
  description = "Security auditing and compliance monitoring access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "securityhub:*",
          "guardduty:*",
          "config:*",
          "cloudtrail:*",
          "access-analyzer:*",
          "inspector:*",
          "macie:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::hms-${var.environment}-audit-logs/*",
          "arn:aws:s3:::hms-${var.environment}-security-events/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:FilterLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${var.account_id}:log-group:/hms/${var.environment}/security:*"
      }
    ]
  })
}

# Emergency Access Policy
resource "aws_iam_policy" "emergency_access_policy" {
  name        = "hms-emergency-access-policy"
  description = "Emergency break-glass access for critical situations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:*",
          "rds:*",
          "s3:*",
          "kms:*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:PrincipalTag/EmergencyAccess" = "true"
          },
          DateGreaterThan = {
            "aws:CurrentTime" = "${timestamp()}"
          },
          DateLessThan = {
            "aws:CurrentTime" = "${timeadd(timestamp(), \"1h\")}"
          }
        }
      }
    ]
  })
}