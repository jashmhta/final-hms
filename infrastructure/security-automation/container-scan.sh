#!/bin/bash
set -e
services=(patient-service auth-service billing-service appointment-service prescription-service lab-service imaging-service pharmacy-service nurse-service doctor-service admin-service reporting-service analytics-service notification-service scheduling-service emr-service ehr-service telehealth-service payment-service insurance-service claims-service inventory-service hr-service finance-service compliance-service audit-service security-service integration-service api-gateway frontend-service database-service)
for service in "${services[@]}"; do
    echo "Scanning $service..."
    trivy image --severity HIGH,CRITICAL --exit-code 1 --no-progress hms/$service:latest
    trivy image --format json --output trivy-$service.json hms/$service:latest
    jq -r '.Results[] | select(.Vulnerabilities[] | .Severity == "HIGH" or .Severity == "CRITICAL") | .Target' trivy-$service.json > high-risk-$service.txt
    if [ -s high-risk-$service.txt ]; then
        echo "WARNING: High/Critical vulnerabilities found in $service"
        cat high-risk-$service.txt
    fi
done
echo "HIPAA Compliance Scan Summary" > compliance-report.txt
echo "Generated: $(date)" >> compliance-report.txt
echo "Total services scanned: ${
cat compliance-report.txt
echo "Container security scan complete"