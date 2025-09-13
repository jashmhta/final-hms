resource "aws_cloudwatch_log_group" "security_logs" {
  name              = "/aws/security/hms-${var.environment}"
  retention_in_days = 365  # HIPAA requirement

  tags = {
    Name  = "hms-security-logs"
    HIPAA = "true"
  }
}

resource "aws_iam_policy" "security_audit" {
  name = "hms-security-audit-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "cloudtrail:LookupEvents"
        ]
        Resource = "*"
      }
    ]
  })
}
