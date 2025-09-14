# Deployment Guide

This guide provides comprehensive instructions for deploying the HMS (Healthcare Management System) in enterprise environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [AWS Deployment](#aws-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Security Hardening](#security-hardening)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ or CentOS 7+)
- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 100GB+ SSD storage
- **Network**: 1Gbps+ bandwidth

### Software Dependencies

- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- Helm 3.0+ (for K8s deployment)
- Terraform 1.0+ (for infrastructure provisioning)
- AWS CLI 2.0+ (for AWS deployment)

### Network Requirements

- **Inbound Ports**:
  - 80/443 (HTTP/HTTPS)
  - 22 (SSH - restrict to admin IPs)
  - 5432 (PostgreSQL - internal only)
  - 6379 (Redis - internal only)
  - 9090 (Prometheus - monitoring)
  - 3000 (Grafana - monitoring)

- **Outbound Ports**:
  - 443 (HTTPS for external APIs)
  - 587/465 (SMTP for email notifications)

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/hms-enterprise.git
cd hms-enterprise
```

### 2. Environment Configuration

Create environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database
POSTGRES_DB=hms
POSTGRES_USER=hms_user
POSTGRES_PASSWORD=strong-db-password-2024
POSTGRES_HOST=localhost

# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
```

### 3. Docker Compose Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Database Migration

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

### 5. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/

## Docker Deployment

### Production Docker Compose

Use the provided `docker-compose.prod.yml`:

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With custom environment
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml hms

# Check services
docker service ls
```

### Multi-Stage Build

The Dockerfile uses multi-stage builds for optimization:

```dockerfile
# Build stage
FROM python:3.12-slim as builder
# ... build dependencies

# Production stage
FROM python:3.12-slim as production
# ... runtime only
```

## Kubernetes Deployment

### 1. Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz -o helm.tar.gz
tar -zxvf helm.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/
```

### 2. Deploy with Helm

```bash
# Add Helm repository
helm repo add hms https://charts.hms-enterprise.com
helm repo update

# Install HMS
helm install hms hms/hms \
  --namespace hms \
  --create-namespace \
  --values values-prod.yaml
```

### 3. Manual Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace hms

# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/database-config.yaml
kubectl apply -f k8s/security-policies.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check deployment
kubectl get pods -n hms
kubectl get services -n hms
```

### 4. Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hms-ingress
  namespace: hms
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - hms.yourdomain.com
    secretName: hms-tls
  rules:
  - host: hms.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

## AWS Deployment

### 1. Infrastructure Setup with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file=prod.tfvars

# Apply changes
terraform apply -var-file=prod.tfvars
```

### 2. ECS Deployment

```bash
# Build and push images
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker build -t hms-backend .
docker tag hms-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/hms-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/hms-backend:latest

# Deploy to ECS
aws ecs update-service --cluster hms-cluster --service hms-backend --force-new-deployment
```

### 3. RDS Setup

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier hms-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username hms \
  --master-user-password <password> \
  --allocated-storage 100 \
  --vpc-security-group-ids <security-group> \
  --db-subnet-group-name <subnet-group>
```

### 4. ElastiCache Setup

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id hms-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

## Production Configuration

### Environment Variables

```bash
# Security
DJANGO_SECRET_KEY=<strong-random-key>
DJANGO_DEBUG=False
ALLOWED_HOSTS=hms.yourdomain.com,api.hms.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# Email
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_USER=noreply@yourdomain.com
EMAIL_PASSWORD=<app-password>

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
PROMETHEUS_PUSHGATEWAY_URL=http://prometheus-pushgateway:9091

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name hms.yourdomain.com;

    ssl_certificate /etc/ssl/certs/hms.crt;
    ssl_certificate_key /etc/ssl/private/hms.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring Setup

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'hms-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'hms-frontend'
    static_configs:
      - targets: ['frontend:3000']
```

### Grafana Setup

```bash
# Access Grafana
# Default credentials: admin/admin
# URL: http://grafana.yourdomain.com

# Import dashboards
# - HMS Backend Dashboard (ID: 12345)
# - HMS Frontend Dashboard (ID: 12346)
# - System Metrics Dashboard (ID: 12347)
```

### Alerting Rules

```yaml
groups:
  - name: hms_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: DatabaseConnectionIssues
        expr: pg_stat_activity_count{state="idle"} > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of idle database connections"
```

## Security Hardening

### 1. Network Security

```bash
# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### 2. SSL/TLS Setup

```bash
# Generate SSL certificate
sudo certbot --nginx -d hms.yourdomain.com

# Or use custom certificate
sudo cp hms.crt /etc/ssl/certs/
sudo cp hms.key /etc/ssl/private/
```

### 3. Database Security

```sql
-- Create application user
CREATE USER hms_app WITH PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE hms TO hms_app;
GRANT USAGE ON SCHEMA public TO hms_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hms_app;

-- Enable row-level security
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
CREATE POLICY patient_policy ON patients FOR ALL USING (tenant_id = current_tenant_id());
```

### 4. Application Security

```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
```

### 5. Backup Security

```bash
# Encrypt backups
openssl enc -aes-256-cbc -salt -in backup.sql -out backup.sql.enc -k <encryption-key>

# Secure backup storage
aws s3 cp backup.sql.enc s3://hms-backups/ --sse AES256
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database connectivity
   docker-compose exec db psql -U hms -d hms

   # Verify environment variables
   docker-compose exec backend env | grep DATABASE
   ```

2. **Redis Connection Issues**
   ```bash
   # Test Redis connection
   docker-compose exec redis redis-cli ping

   # Check Redis logs
   docker-compose logs redis
   ```

3. **Application Not Starting**
   ```bash
   # Check application logs
   docker-compose logs backend

   # Verify dependencies
   docker-compose exec backend pip list
   ```

### Performance Tuning

```bash
# Database optimization
docker-compose exec db psql -U hms -d hms -c "VACUUM ANALYZE;"

# Redis memory optimization
docker-compose exec redis redis-cli CONFIG SET maxmemory 256mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Support

For deployment support:
- Check logs: `docker-compose logs -f`
- Monitor metrics: `http://grafana.yourdomain.com`
- Review alerts: `http://alertmanager.yourdomain.com`
- Contact DevOps team
