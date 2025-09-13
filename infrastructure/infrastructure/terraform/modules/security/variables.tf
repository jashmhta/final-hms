variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "cluster_arn" {
  description = "ECS cluster ARN"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}
