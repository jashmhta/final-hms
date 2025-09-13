group "default" {
  targets = [
    "backend",
    "frontend",
    "price_estimator",
    "bed_management",
    "triage",
    "analytics_service",
    "notifications",
    "radiology",
    "feedback",
    "consent",
    "audit",
    "er_alerts",
    "ot_scheduling",
    "graphql_gateway",
  ]
}

target "backend" {
  context = "."
  dockerfile = "backend/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-backend:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-backend:${GITHUB_SHA}",
  ]
}

target "frontend" {
  context = "frontend"
  dockerfile = "frontend/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-frontend:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-frontend:${GITHUB_SHA}",
  ]
}

target "price_estimator" {
  context = "services/price_estimator"
  dockerfile = "services/price_estimator/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-price-estimator:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-price-estimator:${GITHUB_SHA}",
  ]
}

target "bed_management" {
  context = "services/bed_management"
  dockerfile = "services/bed_management/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-bed-management:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-bed-management:${GITHUB_SHA}",
  ]
}

target "triage" {
  context = "services/triage"
  dockerfile = "services/triage/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-triage:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-triage:${GITHUB_SHA}",
  ]
}

target "analytics_service" {
  context = "services/analytics_service"
  dockerfile = "services/analytics_service/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-analytics:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-analytics:${GITHUB_SHA}",
  ]
}

target "notifications" {
  context = "services/notifications"
  dockerfile = "services/notifications/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-notifications:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-notifications:${GITHUB_SHA}",
  ]
}

target "radiology" {
  context = "services/radiology"
  dockerfile = "services/radiology/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-radiology:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-radiology:${GITHUB_SHA}",
  ]
}

target "feedback" {
  context = "services/feedback"
  dockerfile = "services/feedback/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-feedback:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-feedback:${GITHUB_SHA}",
  ]
}

target "consent" {
  context = "services/consent"
  dockerfile = "services/consent/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-consent:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-consent:${GITHUB_SHA}",
  ]
}

target "audit" {
  context = "services/audit"
  dockerfile = "services/audit/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-audit:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-audit:${GITHUB_SHA}",
  ]
}

target "graphql_gateway" {
  context = "services/graphql_gateway"
  dockerfile = "services/graphql_gateway/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-graphql-gateway:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-graphql-gateway:${GITHUB_SHA}",
  ]
}

target "er_alerts" {
  context = "services/er_alerts"
  dockerfile = "services/er_alerts/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-er-alerts:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-er-alerts:${GITHUB_SHA}",
  ]
}

target "ot_scheduling" {
  context = "services/ot_scheduling"
  dockerfile = "services/ot_scheduling/Dockerfile"
  tags = [
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-ot-scheduling:latest",
    "ghcr.io/${GITHUB_REPOSITORY_OWNER}/newhms-ot-scheduling:${GITHUB_SHA}",
  ]
}
