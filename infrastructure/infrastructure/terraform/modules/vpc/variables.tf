variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "public_subnets" {
  description = "Public subnets CIDR blocks"
  type        = list(string)
}

variable "private_subnets" {
  description = "Private subnets CIDR blocks"
  type        = list(string)
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
}

variable "environment" {
  description = "Environment"
  type        = string
}
