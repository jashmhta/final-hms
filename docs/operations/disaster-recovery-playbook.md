# HMS Disaster Recovery Playbook

## Table of Contents
1. [Emergency Response Procedures](#emergency-response-procedures)
2. [Failover Procedures](#failover-procedures)
3. [Recovery Procedures](#recovery-procedures)
4. [Communication Protocols](#communication-protocols)
5. [Testing and Validation](#testing-and-validation)
6. [Post-Incident Review](#post-incident-review)

## Emergency Response Procedures

### Incident Classification

#### Severity Levels
- **SEV-0 (Critical)**: Complete system outage affecting all patients
- **SEV-1 (Major)**: Regional outage affecting multiple services
- **SEV-2 (Minor)**: Single service outage affecting some patients
- **SEV-3 (Low)**: Performance degradation or limited impact

#### Response Times
- **SEV-0**: Immediate response (< 5 minutes)
- **SEV-1**: 15-minute response time
- **SEV-2**: 30-minute response time
- **SEV-3**: 1-hour response time

### Emergency Contacts

#### Primary Contacts
- **Incident Commander**: [Name] - [Phone] - [Email]
- **Technical Lead**: [Name] - [Phone] - [Email]
- **Operations Manager**: [Name] - [Phone] - [Email]
- **Security Lead**: [Name] - [Phone] - [Email]

#### Backup Contacts
- **Backup Incident Commander**: [Name] - [Phone] - [Email]
- **Backup Technical Lead**: [Name] - [Phone] - [Email]

### Incident Response Checklist

#### Initial Response (0-5 minutes)
1. **Declare Incident**: Use incident response channel
2. **Activate Team**: Notify all response team members
3. **Assess Impact**: Determine scope and severity
4. **Initial Communication**: Send initial notification to stakeholders
5. **Set Up War Room**: Create dedicated communication channel
6. **Document Everything**: Start incident log

#### Assessment Phase (5-15 minutes)
1. **Gather Information**: Collect logs, metrics, and error reports
2. **Identify Root Cause**: Determine what caused the incident
3. **Assess Impact**: Determine affected services and users
4. **Identify Mitigation**: Determine immediate mitigation steps
5. **Estimate Timeline**: Provide initial ETA for resolution

#### Mitigation Phase (15-60 minutes)
1. **Implement Mitigation**: Apply immediate fixes
2. **Monitor Progress**: Track effectiveness of mitigation
3. **Update Stakeholders**: Provide regular updates
4. **Prepare for Failover**: If needed, prepare failover procedures
5. **Document Actions**: Record all mitigation steps

## Failover Procedures

### Automated Failover

#### Trigger Conditions
- Primary region becomes unreachable for > 5 minutes
- Critical services unavailable for > 10 minutes
- Database corruption detected
- Natural disaster declared in primary region

#### Failover Process
1. **Detection**: Failover controller detects failure
2. **Verification**: Health checks confirm failure
3. **Promotion**: Secondary region promoted to primary
4. **DNS Update**: Route 53 records updated
5. **Service Scaling**: Services scale up in new primary
6. **Notification**: Automated notifications sent

#### Manual Failover

#### Prerequisites
- Verify secondary region is healthy
- Ensure replication lag is < 30 seconds
- Confirm backup data is current
- Prepare rollback plan

#### Steps
1. **Preparation**
   ```bash
   # Check secondary region health
   kubectl get nodes --context=us-west-2
   kubectl get pods --all-namespaces --context=us-west-2

   # Check database replication
   psql -h postgres-secondary.hms.system.svc.cluster.local -U postgres -c "SELECT * FROM pg_stat_replication;"

   # Check application health
   curl -f https://api-secondary.hms.enterprise.com/health
   ```

2. **Failover Execution**
   ```bash
   # Execute failover script
   ./scripts/failover-region.sh us-east-1 us-west-2

   # Monitor failover progress
   kubectl get pods --all-namespaces --context=us-west-2 -w

   # Verify services are running
   kubectl get deployments --all-namespaces --context=us-west-2
   ```

3. **Post-Failover Validation**
   ```bash
   # Test critical services
   curl -f https://api.hms.enterprise.com/patient-service/health
   curl -f https://api.hms.enterprise.com/appointment-service/health
   curl -f https://api.hms.enterprise.com/clinical-service/health

   # Verify data consistency
   psql -h postgres-primary.hms.system.svc.cluster.local -U postgres -c "SELECT COUNT(*) FROM patients;"
   ```

### Database Failover

#### PostgreSQL Failover
1. **Stop Primary** (if accessible)
   ```bash
   kubectl exec -it postgres-primary-0 -n hms-system -- pg_ctl stop -D /var/lib/postgresql/data
   ```

2. **Promote Secondary**
   ```bash
   kubectl exec -it postgres-secondary-0 -n hms-system -- pg_ctl promote -D /var/lib/postgresql/data
   ```

3. **Update Application Configuration**
   ```bash
   kubectl set env deployment/* --all -n hms-system DATABASE_HOST=postgres-secondary.hms.system.svc.cluster.local
   ```

4. **Verify Replication**
   ```bash
   kubectl exec -it postgres-secondary-0 -n hms-system -- psql -U postgres -c "SELECT * FROM pg_stat_replication;"
   ```

#### Redis Failover
1. **Promote Redis Replica**
   ```bash
   kubectl exec -it redis-secondary-0 -n hms-system -- redis-cli SLAVEOF NO ONE
   ```

2. **Update Application Configuration**
   ```bash
   kubectl set env deployment/* --all -n hms-system REDIS_HOST=redis-secondary.hms.system.svc.cluster.local
   ```

3. **Verify Redis Status**
   ```bash
   kubectl exec -it redis-secondary-0 -n hms-system -- redis-cli INFO replication
   ```

### Service Failover

#### Kubernetes Service Updates
1. **Update Service Endpoints**
   ```bash
   # Update all services to point to new region
   kubectl get svc --all-namespaces -o json | jq '.items[] | select(.spec.type == "LoadBalancer") | .metadata.name'
   ```

2. **Update Ingress Configuration**
   ```bash
   kubectl get ingress --all-namespaces -o yaml
   ```

3. **Verify Service Connectivity**
   ```bash
   # Test all critical endpoints
   for service in patient appointment clinical billing auth; do
     curl -f https://api.hms.enterprise.com/${service}-service/health
   done
   ```

## Recovery Procedures

### Primary Region Recovery

#### Pre-Recovery Checks
1. **Verify Infrastructure**: Check cloud provider status
2. **Check Connectivity**: Verify network connectivity
3. **Assess Damage**: Determine what needs to be restored
4. **Plan Recovery**: Create recovery plan

#### Database Recovery
1. **Restore from Backup**
   ```bash
   # Get latest backup
   LATEST_BACKUP=$(aws s3 ls s3://hms-backups-us-east-1/databases/ --region us-east-1 | sort | tail -1 | awk '{print $4}')

   # Restore database
   ./scripts/restore-database.sh ${LATEST_BACKUP}
   ```

2. **Configure Replication**
   ```bash
   # Set up replication from new primary
   kubectl exec -it postgres-primary-0 -n hms-system -- psql -U postgres -c "SELECT * FROM pg_create_physical_replication_slot('us_east_1_slot');"
   ```

3. **Verify Data Consistency**
   ```bash
   # Compare data counts
   psql -h postgres-primary.hms.system.svc.cluster.local -U postgres -c "SELECT COUNT(*) FROM patients;"
   psql -h postgres-secondary.hms.system.svc.cluster.local -U postgres -c "SELECT COUNT(*) FROM patients;"
   ```

#### Application Recovery
1. **Deploy Applications**
   ```bash
   # Restore Kubernetes resources
   ./scripts/restore-kubernetes.sh kubernetes_backup_$(date +%Y%m%d).tar.gz
   ```

2. **Verify Applications**
   ```bash
   # Check all pods are running
   kubectl get pods --all-namespaces --context=us-east-1

   # Test application endpoints
   curl -f https://api-primary.hms.enterprise.com/health
   ```

### Switchover Back to Primary

#### Pre-Switchover Checks
1. **Verify Primary Health**: Ensure primary region is stable
2. **Check Replication**: Verify replication is current
3. **Prepare for Switchover**: Plan switchover steps
4. **Notify Stakeholders**: Inform about planned switchover

#### Switchover Execution
1. **Gradual Traffic Shift**
   ```bash
   # Update DNS weights gradually
   # 80% secondary, 20% primary
   # 60% secondary, 40% primary
   # 40% secondary, 60% primary
   # 20% secondary, 80% primary
   # 0% secondary, 100% primary
   ```

2. **Monitor Performance**
   ```bash
   # Monitor latency and error rates
   curl -s https://prometheus.hms.enterprise.com/api/v1/query?query=rate(http_requests_total[5m])
   ```

3. **Final Verification**
   ```bash
   # Verify all services are functioning
   ./scripts/health-check.sh
   ```

## Communication Protocols

### Internal Communication

#### Incident Response Channel
- **Primary**: Slack channel #incident-response
- **Backup**: Microsoft Teams channel
- **Escalation**: Phone call to incident commander

#### Status Updates
- **Initial**: Within 5 minutes of incident detection
- **Updates**: Every 15 minutes during active incident
- **Resolution**: Within 30 minutes of resolution

### External Communication

#### Stakeholder Communication
- **Clinical Staff**: Email and SMS alerts
- **Administrative Staff**: Email alerts
- **Patients**: Website banner and automated messages
- **Partners**: Direct communication through established channels

#### Communication Templates

#### Initial Incident Alert
```
SUBJECT: [SEV-X] HMS System Incident - Initial Alert

INCIDENT DETAILS:
- Time: [Timestamp]
- Severity: [Severity Level]
- Impact: [Description of impact]
- Services Affected: [List of affected services]
- Current Status: [Current status]

NEXT STEPS:
- [Immediate actions being taken]
- ETA for next update: [Time]

CONTACT:
- Incident Commander: [Name/Contact]
- Technical Lead: [Name/Contact]
```

#### Status Update
```
SUBJECT: [SEV-X] HMS System Incident - Status Update

INCIDENT STATUS:
- Duration: [Duration]
- Severity: [Severity Level]
- Progress: [What has been accomplished]
- Issues: [Current challenges]
- Next Steps: [Planned actions]

IMPACT ASSESSMENT:
- Patients Affected: [Number/Description]
- Services Impacted: [Current status]
- Workarounds: [Available workarounds]

NEXT UPDATE: [Time]
```

#### Resolution Notification
```
SUBJECT: [SEV-X] HMS System Incident - RESOLVED

INCIDENT RESOLVED:
- Resolution Time: [Timestamp]
- Duration: [Total duration]
- Root Cause: [Summary of root cause]
- Resolution: [Summary of resolution]

IMPACT SUMMARY:
- Patients Affected: [Final count]
- Services Impacted: [Final list]
- Data Loss: [Any data loss]

PREVENTIVE ACTIONS:
- [Immediate actions taken]
- [Long-term improvements planned]

POST-MORTEM:
- Post-mortem scheduled for: [Date/Time]
- All stakeholders invited to attend

THANK YOU:
- Thank you for your patience and cooperation during this incident.
```

## Testing and Validation

### Regular Testing

#### Weekly Tests
- **Health Checks**: Verify all systems are operational
- **Backup Verification**: Test backup integrity
- **Replication Status**: Check database replication
- **Performance Tests**: Run basic performance tests

#### Monthly Tests
- **Failover Drills**: Test failover procedures
- **Recovery Tests**: Test recovery procedures
- **Load Tests**: Test system under load
- **Security Tests**: Test security controls

#### Quarterly Tests
- **Full Disaster Recovery**: Complete DR test
- **Performance Benchmarking**: Comprehensive performance testing
- **Compliance Audit**: Verify compliance requirements
- **Capacity Planning**: Review and update capacity plans

### Test Scenarios

#### Scenario 1: Regional Outage
1. **Simulate Failure**: Take primary region offline
2. **Automated Failover**: Verify automatic failover works
3. **Manual Verification**: Verify systems are operational
4. **Recovery**: Restore primary region
5. **Switchover**: Switch back to primary

#### Scenario 2: Database Failure
1. **Simulate Database Failure**: Stop primary database
2. **Failover**: Promote secondary database
3. **Verify Applications**: Verify applications work with new database
4. **Recovery**: Restore primary database
5. **Switchover**: Switch back to primary

#### Scenario 3: Network Partition
1. **Simulate Partition**: Create network partition
2. **Detect Partition**: Verify partition detection works
3. **Mitigate**: Apply mitigation strategies
4. **Resolve**: Resolve partition
5. **Verify**: Verify systems recover

### Test Documentation

#### Test Plan Template
```
TEST PLAN: [Test Name]

OBJECTIVE:
- [What the test aims to verify]

SCOPE:
- Systems Involved: [List of systems]
- Regions Affected: [List of regions]
- Duration: [Expected duration]

PRE-REQUISITES:
- [Requirements for test]
- [Preparations needed]

TEST PROCEDURE:
1. [Step 1]
2. [Step 2]
3. [Step 3]

SUCCESS CRITERIA:
- [What defines success]
- [Metrics to measure]

ROLLBACK PROCEDURE:
- [How to rollback if test fails]

POST-TEST ACTIONS:
- [Cleanup required]
- [Documentation to update]
```

## Post-Incident Review

### Review Process

#### Immediate Review (24-48 hours)
- **Gather Data**: Collect logs, metrics, and timelines
- **Initial Analysis**: Identify immediate causes
- **Create Timeline**: Document incident timeline
- **Initial Findings**: Prepare initial findings

#### Formal Review (1-2 weeks)
- **Stakeholder Meeting**: Review with all stakeholders
- **Root Cause Analysis**: Deep dive into root causes
- **Action Items**: Create action items
- **Documentation**: Update documentation

#### Follow-up Review (1 month)
- **Action Item Status**: Review progress on action items
- **Effectiveness Check**: Verify fixes are effective
- **Process Improvement**: Identify process improvements

### Root Cause Analysis

#### 5 Whys Technique
1. **Why did the incident occur?** [First-level cause]
2. **Why did that happen?** [Second-level cause]
3. **Why did that happen?** [Third-level cause]
4. **Why did that happen?** [Fourth-level cause]
5. **Why did that happen?** [Root cause]

#### Fishbone Diagram
- **People**: Training, staffing, procedures
- **Process**: Automation, monitoring, alerting
- **Technology**: Infrastructure, applications, dependencies
- **Environment**: Configuration, deployment, networking

### Action Items

#### Immediate Actions (0-30 days)
- **Fix Technical Issues**: Address immediate technical problems
- **Update Documentation**: Update relevant documentation
- **Improve Monitoring**: Add monitoring and alerting
- **Training**: Provide necessary training

#### Medium-term Actions (30-90 days)
- **Process Improvements**: Improve incident response processes
- **Infrastructure Improvements**: Upgrade or improve infrastructure
- **Tooling Improvements**: Implement better tools
- **Testing**: Implement better testing procedures

#### Long-term Actions (90+ days)
- **Architecture Changes**: Consider architectural changes
- **Process Re-engineering**: Re-engineer processes
- **Training Programs**: Develop comprehensive training
- **Culture Initiatives**: Improve reliability culture

### Lessons Learned

#### Positive Outcomes
- **What worked well**: Identify successful aspects
- **Team Performance**: Evaluate team performance
- **Tools and Processes**: Evaluate tool effectiveness

#### Areas for Improvement
- **Response Time**: Identify areas where response time can be improved
- **Communication**: Identify communication improvements
- **Technical Skills**: Identify skill gaps
- **Process Gaps**: Identify process improvements

#### Preventive Measures
- **Automation**: Identify opportunities for automation
- **Monitoring**: Improve monitoring and alerting
- **Documentation**: Improve documentation
- **Training**: Improve training programs

## Appendix

### Checklists

#### Pre-Failover Checklist
- [ ] Secondary region health verified
- [ ] Database replication lag < 30 seconds
- [ ] Backup data is current
- [ ] Stakeholders notified
- [ ] Rollback plan prepared
- [ ] Communication channels ready

#### Post-Failover Checklist
- [ ] All services operational in new primary
- [ ] Database replication working
- [ ] DNS records updated
- [ ] Monitoring working
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Stakeholders notified of completion

#### Recovery Checklist
- [ ] Primary region infrastructure restored
- [ ] Database restored and verified
- [ ] Applications deployed and tested
- [ ] Replication configured
- [ ] Performance tested
- [ ] Security verified
- [ ] Documentation updated

### Contact Lists

#### Emergency Contacts
- **Incident Response Team**: [Contact information]
- **Technical Support**: [Contact information]
- **Management**: [Contact information]
- **External Partners**: [Contact information]

#### Vendor Contacts
- **Cloud Provider**: [Contact information]
- **Database Support**: [Contact information]
- **Security Services**: [Contact information]
- **Network Services**: [Contact information]

### Runbooks

#### Database Failover Runbook
- Detailed steps for database failover
- Commands and scripts
- Expected outputs
- Troubleshooting steps

#### Application Recovery Runbook
- Detailed steps for application recovery
- Commands and scripts
- Expected outputs
- Troubleshooting steps

#### Network Recovery Runbook
- Detailed steps for network recovery
- Commands and scripts
- Expected outputs
- Troubleshooting steps

This playbook should be reviewed and updated quarterly to ensure it remains current and effective. All team members should be familiar with its contents and participate in regular drills and testing.