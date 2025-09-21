module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-${var.environment}-vpc"
  cidr = var.vpc_cidr

  azs             = data.aws_availability_zones.available.names
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets
  database_subnets = var.database_subnets

  enable_nat_gateway     = var.enable_nat_gateway
  single_nat_gateway     = var.single_nat_gateway
  one_nat_gateway_per_az = !var.single_nat_gateway

  enable_vpn_gateway = false

  enable_dns_hostnames = true
  enable_dns_support   = true

  enable_flow_log                      = var.enable_vpc_flow_logs
  create_flow_log_cloudwatch_log_group = var.enable_vpc_flow_logs
  flow_log_max_aggregation_interval   = 60

  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"
    "Environment"                              = var.environment
    "Compliance"                               = "HIPAA,HITRUST"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"          = "1"
    "Environment"                              = var.environment
    "Compliance"                               = "HIPAA,HITRUST"
  }

  database_subnet_tags = {
    "Environment" = var.environment
    "Compliance"  = "HIPAA,HITRUST"
  }

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_network_acl" "private" {
  vpc_id = module.vpc.vpc_id

  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  ingress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = {
    "Name"        = "${var.project_name}-private-nacl"
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_network_acl" "public" {
  vpc_id = module.vpc.vpc_id

  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 200
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 300
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  tags = {
    "Name"        = "${var.project_name}-public-nacl"
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_network_acl" "database" {
  vpc_id = module.vpc.vpc_id

  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 5432
    to_port    = 5432
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 200
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 6379
    to_port    = 6379
  }

  tags = {
    "Name"        = "${var.project_name}-database-nacl"
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_network_acl_association" "private" {
  network_acl_id = aws_network_acl.private.id
  subnet_id      = module.vpc.private_subnets[0]
}

resource "aws_network_acl_association" "public" {
  network_acl_id = aws_network_acl.public.id
  subnet_id      = module.vpc.public_subnets[0]
}

resource "aws_network_acl_association" "database" {
  network_acl_id = aws_network_acl.database.id
  subnet_id      = module.vpc.database_subnets[0]
}

resource "aws_vpc_endpoint" "s3" {
  count           = var.enable_s3_endpoint ? 1 : 0
  vpc_id          = module.vpc.vpc_id
  service_name    = "com.amazonaws.${var.aws_region}.s3"
  route_table_ids = module.vpc.private_route_table_ids

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_vpc_endpoint" "dynamodb" {
  count           = var.enable_s3_endpoint ? 1 : 0
  vpc_id          = module.vpc.vpc_id
  service_name    = "com.amazonaws.${var.aws_region}.dynamodb"
  route_table_ids = module.vpc.private_route_table_ids

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type = "Interface"
  subnet_ids        = module.vpc.private_subnets
  security_group_ids = [aws_security_group.vpc_endpoint.id]

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type = "Interface"
  subnet_ids        = module.vpc.private_subnets
  security_group_ids = [aws_security_group.vpc_endpoint.id]

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}

resource "aws_security_group" "vpc_endpoint" {
  name_prefix = "${var.project_name}-vpc-endpoint"
  description = "Security group for VPC endpoints"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "Compliance"  = "HIPAA,HITRUST"
  }
}