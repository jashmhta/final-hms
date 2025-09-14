# Security Documentation

This document outlines the comprehensive security measures implemented in the HMS (Healthcare Management System) enterprise deployment.

## Security Overview

The HMS implements a defense-in-depth security strategy covering:

- **Network Security**: VPC isolation, security groups, WAF
- **Application Security**: Authentication, authorization, input validation
- **Data Security**: Encryption at rest and in transit, access controls
- **Infrastructure Security**: IAM, monitoring, compliance
- **Operational Security**: Incident response, backup security

## Authentication & Authorization

### JWT Authentication

```python
# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### Multi-Factor Authentication (MFA)

```python
# MFA Implementation
class MFAHandler:
    def generate_totp_secret(self):
        return pyotp.random_base32()

    def verify_totp(self, secret, token):
        totp = pyotp.TOTP(secret)
        return totp.verify(token)
```

### Role-Based Access Control (RBAC)

```python
# Permission Classes
class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'doctor'

class IsNurse(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'nurse'
```

## Data Protection

### Encryption at Rest

```python
# Model Field Encryption
class EncryptedCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if value:
            return encrypt(value)
        return value

    def from_db_value(self, value, expression, connection):
        if value:
            return decrypt(value)
        return value
```

### Encryption at Transit

```nginx
# SSL/TLS Configuration
server {
    listen 443 ssl http2;
    server_name hms.yourdomain.com;

    ssl_certificate /etc/ssl/certs/hms.crt;
    ssl_certificate_key /etc/ssl/private/hms.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
}
```

### Data Classification

| Data Type | Classification | Encryption | Retention |
|-----------|----------------|------------|-----------|
| PHI | Restricted | AES-256 | 7 years |
| PII | Confidential | AES-256 | 3 years |
| Financial | Confidential | AES-256 | 7 years |
| Logs | Internal | AES-128 | 1 year |

## Network Security

### VPC Configuration

```hcl
# VPC with Public/Private Subnets
resource "aws_vpc" "hms" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true

  tags = {
    Name = "hms-vpc"
  }
}

resource "aws_subnet" "private" {
  count = 3
  vpc_id = aws_vpc.hms.id
  cidr_block = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "hms-private-${count.index + 1}"
  }
}
```

### Security Groups

```hcl
# Application Load Balancer Security Group
resource "aws_security_group" "alb" {
  name_prefix = "hms-alb-"
  vpc_id = aws_vpc.hms.id

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

# ECS Security Group
resource "aws_security_group" "ecs" {
  name_prefix = "hms-ecs-"
  vpc_id = aws_vpc.hms.id

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
```

### Web Application Firewall (WAF)

```hcl
# AWS WAF Configuration
resource "aws_wafv2_web_acl" "hms" {
  name  = "hms-web-acl"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }
  }
}
```

## Application Security

### Input Validation

```python
# Django Model Validation
class Patient(models.Model):
    first_name = models.CharField(
        max_length=100,
        validators=[validate_name]
    )
    email = models.EmailField(
        validators=[validate_email_domain]
    )
    ssn = models.CharField(
        max_length=11,
        validators=[validate_ssn]
    )
```

### SQL Injection Prevention

```python
# Safe Query Building
def get_patient_by_id(patient_id):
    # Bad - Vulnerable to SQL injection
    # query = f"SELECT * FROM patients WHERE id = {patient_id}"

    # Good - Parameterized query
    return Patient.objects.filter(id=patient_id).first()
```

### XSS Protection

```python
# Template Escaping
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, 'patient_detail.html', {
        'patient': patient,
        'notes': mark_safe(patient.notes)  # Dangerous!
    })

# Safe version
def patient_detail_safe(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, 'patient_detail.html', {
        'patient': patient,
        'notes': patient.notes  # Auto-escaped
    })
```

## Infrastructure Security

### Identity and Access Management (IAM)

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

resource "aws_iam_role_policy" "ecs_execution" {
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/ecs/hms/*"
      }
    ]
  })
}
```

### Secrets Management

```python
# AWS Secrets Manager Integration
import boto3

def get_database_credentials():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='hms/db/credentials')
    return json.loads(response['SecretString'])

# Usage
db_config = get_database_credentials()
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_config['dbname'],
        'USER': db_config['username'],
        'PASSWORD': db_config['password'],
        'HOST': db_config['host'],
        'PORT': db_config['port'],
    }
}
```

## Monitoring & Alerting

### Security Monitoring

```python
# Security Event Logging
import logging

security_logger = logging.getLogger('security')

def log_security_event(event_type, user, details):
    security_logger.info(json.dumps({
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'user': user.username if user else 'anonymous',
        'ip_address': get_client_ip(),
        'details': details
    }))
```

### Intrusion Detection

```yaml
# Prometheus Alert Rules
groups:
  - name: security_alerts
    rules:
      - alert: HighFailedLoginAttempts
        expr: rate(failed_login_attempts_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High rate of failed login attempts detected"

      - alert: UnusualTrafficPattern
        expr: rate(http_requests_total[5m]) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Unusual traffic pattern detected"
```

## Compliance

### HIPAA Compliance

```python
# Audit Logging for HIPAA
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
```

### GDPR Compliance

```python
# Data Subject Rights
class DataSubjectRequest(models.Model):
    REQUEST_TYPES = [
        ('access', 'Access Request'),
        ('rectification', 'Rectification Request'),
        ('erasure', 'Erasure Request'),
        ('restriction', 'Restriction Request'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

## Incident Response

### Incident Response Plan

1. **Detection**: Automated monitoring and alerting
2. **Assessment**: Evaluate impact and scope
3. **Containment**: Isolate affected systems
4. **Recovery**: Restore from backups
5. **Lessons Learned**: Post-incident review

### Automated Response

```python
# Automated Incident Response
def handle_security_incident(incident_type, details):
    # Log incident
    log_security_event('incident_detected', None, {
        'type': incident_type,
        'details': details
    })

    # Notify security team
    send_security_alert(incident_type, details)

    # Automated containment
    if incident_type == 'brute_force':
        block_ip_address(details['ip_address'])
    elif incident_type == 'sql_injection':
        update_waf_rules(details['pattern'])
```

## Security Testing

### Vulnerability Scanning

```bash
# Container Vulnerability Scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image hms-backend:latest

# Dependency Vulnerability Check
safety check --full-report

# SAST Scanning
bandit -r backend/
```

### Penetration Testing

```bash
# Automated Penetration Testing
docker run --rm -it \
  -v $(pwd)/reports:/reports \
  owasp/zap2docker-stable zap-baseline.py \
  -t https://hms.yourdomain.com \
  -r /reports/zap_report.html
```

## Security Best Practices

### Development

1. **Code Reviews**: All changes require security review
2. **Static Analysis**: Automated security scanning in CI/CD
3. **Dependency Management**: Regular updates and vulnerability checks
4. **Secure Coding**: Follow OWASP guidelines

### Operations

1. **Access Control**: Principle of least privilege
2. **Monitoring**: 24/7 security monitoring
3. **Backup Security**: Encrypted backups with access controls
4. **Incident Response**: Regular drills and updates

### Compliance

1. **Regular Audits**: Quarterly security assessments
2. **Policy Updates**: Annual policy reviews
3. **Training**: Mandatory security training for all staff
4. **Documentation**: Comprehensive security documentation

## Security Checklist

### Pre-Deployment
- [ ] Security groups configured
- [ ] IAM roles with minimal permissions
- [ ] Encryption enabled for data at rest
- [ ] SSL/TLS certificates installed
- [ ] WAF rules configured

### Post-Deployment
- [ ] Vulnerability scanning completed
- [ ] Security monitoring enabled
- [ ] Backup encryption verified
- [ ] Access logs configured
- [ ] Incident response plan tested

### Ongoing
- [ ] Regular security updates
- [ ] Log review and analysis
- [ ] Access control audits
- [ ] Security training completion
- [ ] Compliance monitoring

## Support

For security-related issues:
- **Emergency**: Call security hotline: +1-800-SECURE
- **Email**: security@hms-enterprise.com
- **Documentation**: Internal security wiki
- **Training**: Annual security awareness training
