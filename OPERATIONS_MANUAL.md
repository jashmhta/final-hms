# HMS Enterprise-Grade System Operations Manual

## Table of Contents
1. [Maintenance Procedures](#maintenance-procedures)
2. [Monitoring Dashboards](#monitoring-dashboards)
3. [Compliance Reporting](#compliance-reporting)
4. [Incident Response](#incident-response)
5. [Disaster Recovery](#disaster-recovery)
6. [Change Management](#change-management)

---

## Maintenance Procedures

### Automated Maintenance Tasks

#### Dependency Updates
The system includes automated dependency management for both Python and Node.js packages:

```bash
# Run automated dependency updates
python scripts/automated_dependency_updates.py

# Or use Makefile targets
make auto-fix
```

**Frequency**: Weekly (automated via CI/CD)

**Procedure**:
1. Backup current requirements files
2. Update Python dependencies using pip-compile
3. Update npm packages using npm-check-updates
4. Apply security patches automatically
5. Run comprehensive testing
6. Generate update reports

#### Database Maintenance
```bash
# Database optimization
python scripts/performance/db-optimization.py

# Backup verification
bash scripts/disaster-recovery/backup-verification.sh
```

**Frequency**: Daily for backups, weekly for optimization

#### Code Quality Maintenance
```bash
# Run comprehensive quality analysis
make quality-analysis

# Auto-fix code style issues
make auto-fix

# Security scanning
make security-scan
```

**Frequency**: Pre-commit hooks, daily CI/CD, weekly comprehensive scans

### Manual Maintenance Tasks

#### System Health Checks
```bash
# Multi-region health check
bash scripts/disaster-recovery/health-check.sh

# Performance monitoring
python scripts/performance_monitor.py
```

#### Log Rotation and Cleanup
- Application logs: Rotated daily, retained 30 days
- Audit logs: Retained 7 years (HIPAA compliance)
- Backup logs: Retained 90 days

#### Certificate Management
- SSL certificates: Auto-renewed via cert-manager
- Database certificates: Rotated quarterly
- API keys: Rotated annually

---

## Monitoring Dashboards

### Grafana Dashboards

The system provides comprehensive monitoring through Grafana with the following key dashboards:

#### System Overview Dashboard
- **Metrics**: CPU, Memory, Disk usage across all services
- **Location**: `http://grafana.hms.local/d/system-overview`
- **Refresh Rate**: 30 seconds

#### Application Performance Dashboard
- **Metrics**: Response times, throughput, error rates
- **APIs Monitored**: All microservices endpoints
- **Alerts**: Configured for >5% error rate, >2s response time

#### Database Performance Dashboard
- **Metrics**: Query performance, connection pools, replication lag
- **Databases**: PostgreSQL primary/standby, Redis clusters

#### Security Monitoring Dashboard
- **Metrics**: Failed authentication attempts, suspicious activities
- **Compliance**: HIPAA audit trail monitoring

### Prometheus Metrics

Key metrics exposed via Prometheus:

```yaml
# Application Metrics
- http_requests_total{status, method, endpoint}
- http_request_duration_seconds{quantile="0.95"}
- application_errors_total{type}

# System Metrics
- cpu_usage_percent
- memory_usage_bytes
- disk_usage_percent

# Business Metrics
- patient_records_processed_total
- appointment_bookings_total
- api_calls_per_minute
```

### Alert Manager Configuration

Critical alerts configured:

- **Service Down**: Any microservice unavailable for >5 minutes
- **High Error Rate**: >5% error rate for >5 minutes
- **Database Issues**: Replication lag >30 seconds
- **Security Events**: Failed auth attempts >10/minute

### ELK Stack Monitoring

- **Elasticsearch**: Log aggregation and search
- **Logstash**: Log processing and enrichment
- **Kibana**: Log visualization and dashboards

---

## Compliance Reporting

### Automated Compliance Checks

The system includes automated compliance validation:

```bash
# Run compliance checks
python compliance/audit_trail.py

# Generate compliance reports
python scripts/generate_comprehensive_final_report.py
```

### Compliance Areas Covered

#### HIPAA Compliance
- **Privacy Rule**: PHI encryption, access controls, audit logging
- **Security Rule**: Technical safeguards, risk analysis, contingency planning
- **Breach Notification**: Detection and reporting procedures

#### HL7/FHIR Compliance
- **HL7 v2 Support**: ADT, ORM, ORU, scheduling messages
- **FHIR Support**: R4 compliance, RESTful APIs, JSON validation

#### GDPR Compliance
- **Data Protection**: Lawfulness, purpose limitation, data minimization
- **Patient Rights**: Access, rectification, erasure, portability

### Compliance Reporting Schedule

- **Daily**: Automated compliance checks
- **Weekly**: Security scanning and vulnerability assessment
- **Monthly**: Comprehensive compliance audit
- **Quarterly**: External auditor review
- **Annually**: Full compliance certification

### Audit Trail Management

```python
# Audit logging example
from compliance.audit_trail import AuditLogger

audit = AuditLogger()
audit.log_event(
    user_id=user.id,
    action="PATIENT_RECORD_ACCESS",
    resource="patient:12345",
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT')
)
```

**Retention**: 7 years for HIPAA compliance
**Encryption**: All audit logs encrypted at rest
**Backup**: Daily backups with integrity verification

---

## Incident Response

### Incident Response Plan

#### Phase 1: Detection and Assessment (0-15 minutes)
1. **Alert Triggered**: Monitoring system detects anomaly
2. **Initial Assessment**: On-call engineer evaluates severity
3. **Incident Declaration**: If critical, declare incident and notify team

#### Phase 2: Containment (15-60 minutes)
1. **Isolate Affected Systems**: Use circuit breakers and load balancers
2. **Stop Data Loss**: Implement emergency backups if needed
3. **Notify Stakeholders**: Internal teams and affected customers

#### Phase 3: Eradication (1-4 hours)
1. **Identify Root Cause**: Use logs and monitoring data
2. **Apply Fix**: Deploy hotfix or rollback
3. **Test Fix**: Validate in staging environment

#### Phase 4: Recovery (4-24 hours)
1. **Restore Services**: Gradual rollout with monitoring
2. **Validate Recovery**: Comprehensive testing
3. **Monitor Closely**: Extended monitoring period

#### Phase 5: Lessons Learned (1-7 days)
1. **Post-Mortem Analysis**: Document incident timeline
2. **Update Procedures**: Improve response plan
3. **Training**: Update team training if needed

### Incident Classification

- **Critical (P0)**: System down, data breach, HIPAA violation
- **High (P1)**: Major service degradation, security vulnerability
- **Medium (P2)**: Partial service issues, performance degradation
- **Low (P3)**: Minor issues, monitoring alerts

### Communication Templates

#### Internal Notification
```
INCIDENT: [Title]
Severity: [P0/P1/P2/P3]
Status: [Investigating/Identified/Resolved]
Impact: [Description]
ETA: [Time estimate]
```

#### External Communication
```
Dear [Customer/User],

We are experiencing [brief description] that may affect [services].
Our team is working to resolve this quickly.
We apologize for any inconvenience.

Status updates will be provided at [communication channel].
```

### Tools and Resources

- **Slack Channels**: #incidents, #security-incidents
- **PagerDuty**: Automated alerting and escalation
- **Jira**: Incident tracking and documentation
- **Zoom**: Incident war room coordination

---

## Disaster Recovery

### Multi-Region Architecture

The system implements automated failover across multiple regions:

#### Primary Region: us-east-1
- **Services**: All microservices active
- **Database**: PostgreSQL primary instance
- **Traffic**: 100% via Route53 DNS

#### Secondary Region: us-west-2
- **Services**: Hot standby, scaled to 50%
- **Database**: PostgreSQL standby with streaming replication
- **Traffic**: 0% until failover

#### Tertiary Region: eu-west-1
- **Services**: Cold standby, minimal instances
- **Database**: Asynchronous replication
- **Traffic**: 0% until failover

### Automated Failover Process

```yaml
# Failover triggers (from multi-region/automated-failover.yaml)
triggers:
  - name: critical_service_failure
    condition: "critical_services_unhealthy >= 3"
    action: failover
  - name: region_unreachable
    condition: "region_connectivity == false"
    action: failover
  - name: database_failure
    condition: "database_unhealthy == true"
    action: failover
```

### Recovery Time Objectives (RTO)

- **Critical Services**: RTO < 5 minutes
- **Database**: RTO < 15 minutes
- **Full System**: RTO < 30 minutes

### Recovery Point Objectives (RPO)

- **Patient Data**: RPO < 5 minutes
- **Transaction Data**: RPO < 1 minute
- **Audit Logs**: RPO < 1 minute

### Backup Strategy

#### Database Backups
```bash
# Automated backup script
bash scripts/disaster-recovery/backup-database.sh

# Backup schedule
- Full backup: Daily at 2 AM
- Incremental: Every 6 hours
- Retention: 30 days locally, 90 days in S3
```

#### Application Backups
- **Kubernetes Manifests**: Version controlled in Git
- **Configuration**: Encrypted and backed up daily
- **SSL Certificates**: Auto-renewed, backed up weekly

### Disaster Recovery Testing

```bash
# Regional failover test
bash scripts/disaster-recovery/failover-region.sh us-east-1 us-west-2

# Restore test
bash scripts/disaster-recovery/automated-restore-test.sh
```

**Frequency**: Monthly DR drills, quarterly full failover tests

---

## Change Management

### Change Request Process

#### Change Types
1. **Emergency Changes**: Security fixes, critical bugs
2. **Standard Changes**: Feature deployments, configuration updates
3. **Normal Changes**: Infrastructure updates, maintenance

#### Change Approval Workflow

1. **Submit Change Request**
   - Use Jira for tracking
   - Include impact assessment
   - Define rollback plan

2. **Technical Review**
   - Code review for development changes
   - Architecture review for infrastructure changes
   - Security review for all changes

3. **CAB Approval**
   - Change Advisory Board reviews high-risk changes
   - Approval required for production deployments

4. **Implementation**
   - Deploy to staging first
   - Automated testing validation
   - Manual verification

5. **Post-Implementation Review**
   - Validate success criteria
   - Document lessons learned
   - Update procedures if needed

### Deployment Pipeline

```yaml
# CI/CD Pipeline Stages
stages:
  - lint: Code quality checks
  - test: Unit and integration tests
  - security: Security scanning
  - build: Container image building
  - deploy-staging: Deploy to staging
  - integration-test: E2E testing
  - deploy-production: Blue-green deployment
  - monitor: Post-deployment monitoring
```

### Rollback Procedures

#### Automated Rollback
```bash
# Kubernetes rollback
kubectl rollout undo deployment/hms-backend

# Database rollback
python scripts/database_rollback.py --migration=20230920_rollback
```

#### Manual Rollback Steps
1. **Stop Traffic**: Route traffic away from affected version
2. **Scale Down**: Reduce problematic deployment to 0
3. **Scale Up**: Increase previous stable version
4. **Verify**: Confirm system stability
5. **Cleanup**: Remove failed deployment

### Change Windows

- **Emergency Changes**: 24/7 approval
- **Standard Changes**: Business hours (9 AM - 5 PM EST)
- **Maintenance Windows**: Saturday 2 AM - 6 AM EST

### Quality Gates

All changes must pass:

- **Code Quality**: 95% test coverage, 0 critical issues
- **Security**: No high/critical vulnerabilities
- **Performance**: No regression >5%
- **Compliance**: All compliance checks pass

### Documentation Requirements

- **Change Documentation**: Update runbooks and procedures
- **Architecture Updates**: Update system diagrams
- **Security Updates**: Update threat models
- **Compliance Updates**: Update compliance matrices

---

## Contact Information

### Operations Team
- **Primary On-Call**: ops@hms.enterprise.com
- **Secondary On-Call**: sre@hms.enterprise.com
- **Management**: it-operations@hms.enterprise.com

### Security Team
- **Security Operations**: security@hms.enterprise.com
- **Compliance Officer**: compliance@hms.enterprise.com

### Development Team
- **DevOps Lead**: devops@hms.enterprise.com
- **Backend Lead**: backend@hms.enterprise.com
- **Frontend Lead**: frontend@hms.enterprise.com

### External Contacts
- **Cloud Provider Support**: aws-support@hms.enterprise.com
- **Vendor Support**: vendor-support@hms.enterprise.com

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-09-28 | Operations Team | Initial comprehensive operations manual |
| 1.1 | 2025-09-28 | Operations Team | Added monitoring dashboards section |
| 1.2 | 2025-09-28 | Operations Team | Enhanced incident response procedures |

---

*This operations manual is maintained in the HMS repository at `OPERATIONS_MANUAL.md` and should be updated with any process changes.*