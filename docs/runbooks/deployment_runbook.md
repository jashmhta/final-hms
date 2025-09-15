# Deployment Runbook

## Overview

This runbook provides step-by-step procedures for deploying the Healthcare Management System (HMS) in various environments.

## Prerequisites

### Infrastructure Requirements

- Kubernetes cluster (v1.24+)
- PostgreSQL 15+ database
- Redis 7+ cache
- Kafka 3.0+ message broker
- Load balancer with SSL termination
- Object storage (S3-compatible)

### Software Requirements

- Docker 20.10+
- kubectl 1.24+
- Helm 3.8+
- Terraform 1.0+

## Environment Setup

### 1. Infrastructure Provisioning

```bash
# Clone infrastructure repository
git clone https://github.com/your-org/hms-infrastructure.git
cd hms-infrastructure

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file=environments/production.tfvars

# Apply infrastructure
terraform apply -var-file=environments/production.tfvars
```

### 2. Kubernetes Cluster Setup

```bash
# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name hms-production

# Verify cluster access
kubectl get nodes

# Install required operators
kubectl apply -f operators/
```

### 3. Database Setup

```bash
# Create databases
kubectl apply -f database/postgresql-init.yaml

# Run migrations
kubectl exec -it postgresql-0 -- psql -U postgres -c "CREATE DATABASE hms_main;"
kubectl exec -it postgresql-0 -- psql -U postgres -c "CREATE DATABASE hms_analytics;"

# Initialize schemas
kubectl apply -f database/schemas/
```

## Application Deployment

### 1. Backend Deployment

```bash
# Deploy backend services
kubectl apply -f k8s/backend/

# Wait for deployment
kubectl rollout status deployment/hms-backend

# Verify health
curl https://api.hms.example.com/health/
```

### 2. Frontend Deployment

```bash
# Build and push frontend image
docker build -t hms-frontend:latest frontend/
docker push hms-frontend:latest

# Deploy frontend
kubectl apply -f k8s/frontend/

# Verify deployment
kubectl get pods -l app=hms-frontend
```

### 3. Microservices Deployment

```bash
# Deploy all microservices
for service in patients appointments billing pharmacy lab radiology; do
  kubectl apply -f k8s/services/$service/
  kubectl rollout status deployment/hms-$service
done
```

## Configuration

### 1. Environment Variables

```bash
# Create secrets
kubectl create secret generic hms-secrets \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=REDIS_URL=redis://... \
  --from-literal=KAFKA_BROKERS=... \
  --from-literal=JWT_SECRET=...

# Apply configuration
kubectl apply -f k8s/config/
```

### 2. Ingress Setup

```bash
# Configure ingress
kubectl apply -f k8s/ingress/

# Verify SSL certificate
kubectl get certificate
```

## Data Migration

### 1. Initial Data Load

```bash
# Run data migrations
kubectl exec -it hms-backend-0 -- python manage.py migrate

# Load reference data
kubectl exec -it hms-backend-0 -- python manage.py loaddata initial_data.json

# Seed demo data (optional)
kubectl exec -it hms-backend-0 -- python manage.py seed_demo
```

### 2. User Setup

```bash
# Create initial admin user
kubectl exec -it hms-backend-0 -- python manage.py createsuperuser \
  --username admin \
  --email admin@hms.example.com \
  --noinput

# Set admin password
kubectl exec -it hms-backend-0 -- python manage.py changepassword admin
```

## Monitoring Setup

### 1. Prometheus and Grafana

```bash
# Install monitoring stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack

# Configure dashboards
kubectl apply -f monitoring/dashboards/
```

### 2. Logging

```bash
# Install ELK stack
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch
helm install kibana elastic/kibana
helm install filebeat elastic/filebeat
```

## Testing

### 1. Health Checks

```bash
# Test all endpoints
curl https://api.hms.example.com/health/
curl https://api.hms.example.com/api/schema/

# Test microservices
for service in patients appointments billing; do
  curl https://$service.hms.example.com/health/
done
```

### 2. Load Testing

```bash
# Run load tests
kubectl apply -f load-tests/
kubectl logs -f job/hms-load-test
```

## Rollback Procedures

### 1. Application Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/hms-backend

# Rollback to specific version
kubectl rollout undo deployment/hms-backend --to-revision=2
```

### 2. Database Rollback

```bash
# Create backup before changes
kubectl exec postgresql-0 -- pg_dump hms_main > backup.sql

# Restore from backup
kubectl exec -i postgresql-0 -- psql hms_main < backup.sql
```

## Post-Deployment Tasks

### 1. Security Hardening

```bash
# Apply security policies
kubectl apply -f security/

# Run security scans
kubectl apply -f security/scans/
```

### 2. Performance Optimization

```bash
# Configure autoscaling
kubectl apply -f k8s/hpa/

# Set up caching
kubectl apply -f k8s/cache/
```

### 3. Documentation Update

- Update DNS records
- Configure monitoring alerts
- Set up backup schedules
- Document environment-specific configurations

## Troubleshooting

### Common Issues

- **Pod crashes**: Check logs with `kubectl logs`
- **Service unavailable**: Verify ingress configuration
- **Database connection**: Check secrets and network policies
- **SSL issues**: Verify certificate validity

### Emergency Contacts

- DevOps Team: devops@hms.example.com
- Database Admin: dba@hms.example.com
- Security Team: security@hms.example.com

## Maintenance

### Regular Tasks

- Daily: Monitor alerts and logs
- Weekly: Review performance metrics
- Monthly: Apply security patches
- Quarterly: Major version updates

### Backup Verification

```bash
# Test backup restoration
kubectl apply -f backup/restore-test.yaml
kubectl logs job/backup-restore-test
```