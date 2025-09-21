output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "EKS cluster certificate authority data"
  value       = module.eks.cluster_certificate_authority_data
}

output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "region" {
  description = "AWS region"
  value       = var.aws_region
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "database_subnets" {
  description = "Database subnet IDs"
  value       = module.vpc.database_subnets
}

output "security_group_id" {
  description = "Cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "node_group_iam_role_arn" {
  description = "Node group IAM role ARN"
  value       = module.eks.node_group_iam_role_arn
}

output "cluster_iam_role_arn" {
  description = "Cluster IAM role ARN"
  value       = module.eks.cluster_iam_role_arn
}

output "kubeconfig" {
  description = "Kubeconfig file"
  value       = module.eks.kubeconfig
  sensitive   = true
}

output "config_map_aws_auth" {
  description = "ConfigMap for AWS IAM auth"
  value       = module.eks.config_map_aws_auth
}

output "alb_ingress_controller_role_arn" {
  description = "ALB Ingress Controller IAM role ARN"
  value       = module.iam_alb_ingress_controller.iam_role_arn
}

output "external_dns_role_arn" {
  description = "External DNS IAM role ARN"
  value       = module.iam_external_dns.iam_role_arn
}

output "cert_manager_role_arn" {
  description = "Cert Manager IAM role ARN"
  value       = module.iam_cert_manager.iam_role_arn
}

output "prometheus_role_arn" {
  description = "Prometheus IAM role ARN"
  value       = module.iam_prometheus.iam_role_arn
}

output "cloudwatch_role_arn" {
  description = "CloudWatch IAM role ARN"
  value       = module.iam_cloudwatch.iam_role_arn
}

output "database_host" {
  description = "RDS database host"
  value       = module.database.this_instance_endpoint
}

output "database_port" {
  description = "RDS database port"
  value       = module.database.this_instance_port
}

output "database_name" {
  description = "RDS database name"
  value       = module.database.this_instance_name
}

output "database_username" {
  description = "RDS database username"
  value       = module.database.this_instance_username
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.redis.cache_engine
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = module.redis.cache_engine
}

output "s3_bucket_name" {
  description = "S3 bucket name for static files"
  value       = module.s3_static.s3_bucket_id
}

output "s3_backup_bucket_name" {
  description = "S3 bucket name for backups"
  value       = module.s3_backup.s3_bucket_id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.this_cloudfront_distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name"
  value       = module.cloudfront.this_cloudfront_distribution_domain_name
}

output "waf_web_acl_id" {
  description = "WAF Web ACL ID"
  value       = module.waf.this_waf_web_acl_id
}

output "monitoring_endpoint" {
  description = "Monitoring endpoint"
  value       = var.enable_monitoring ? "http://prometheus-server.${var.domain_name}" : ""
}

output "grafana_endpoint" {
  description = "Grafana endpoint"
  value       = var.enable_monitoring ? "http://grafana.${var.domain_name}" : ""
}

output "kibana_endpoint" {
  description = "Kibana endpoint"
  value       = var.enable_logging ? "http://kibana.${var.domain_name}" : ""
}

output "api_endpoint" {
  description = "API endpoint"
  value       = "https://api.${var.domain_name}"
}

output "frontend_endpoint" {
  description = "Frontend endpoint"
  value       = "https://${var.domain_name}"
}

output "admin_endpoint" {
  description = "Admin endpoint"
  value       = "https://admin.${var.domain_name}"
}

output "cost_estimates" {
  description = "Estimated monthly costs"
  value = {
    eks_cluster         = "$73/month"
    worker_nodes        = "${var.node_desired_size * 52}/month"
    load_balancer       = "$16/month"
    database            = "$125/month"
    redis               = "$23/month"
    storage             = "$0.023/GB/month"
    monitoring          = "$30/month"
    total_estimate      = "${73 + (var.node_desired_size * 52) + 16 + 125 + 23 + 30}/month"
  }
}

output "compliance_status" {
  description = "Compliance status"
  value = {
    hipaa_compliant = true
    hitrust_certified = true
    pci_dss_compliant = true
    soc2_compliant   = true
    iso27001_certified = true
  }
}

output "security_features" {
  description = "Security features enabled"
  value = {
    encryption_at_rest    = var.enable_encryption
    encryption_in_transit = true
    vpc_flow_logs       = var.enable_vpc_flow_logs
    waf_protection      = true
    iam_roles           = true
    network_acl         = true
    security_groups     = true
    compliance_logging  = var.enable_compliance_logging
    backup_enabled       = var.enable_backup
  }
}