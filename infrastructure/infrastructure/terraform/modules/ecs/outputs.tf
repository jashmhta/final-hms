output "cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "service_arns" {
  description = "ECS service ARNs"
  value = { for k, v in aws_ecs_service.hms_service : k => v.arn }
}
