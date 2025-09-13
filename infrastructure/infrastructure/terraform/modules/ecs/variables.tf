variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "db_endpoint" {
  description = "Database endpoint"
  type        = string
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "services" {
  description = "List of services"
  type        = set(string)
  default     = ["patient-service", "auth-service", "billing-service"]
}

variable "environment" {
  description = "Environment"
  type        = string
}
