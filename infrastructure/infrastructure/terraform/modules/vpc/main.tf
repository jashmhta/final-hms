resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "hms-vpc-${var.environment}"
    HIPAA = "true"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "hms-igw-${var.environment}"
  }
}

resource "aws_subnet" "public" {
  count = length(var.public_subnets)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "hms-public-${var.availability_zones[count.index]}"
    Type = "Public"
    HIPAA = "true"
  }
}

resource "aws_subnet" "private" {
  count = length(var.private_subnets)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnets[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = false

  tags = {
    Name = "hms-private-${var.availability_zones[count.index]}"
    Type = "Private"
    HIPAA = "true"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "hms-public-rt-${var.environment}"
    HIPAA = "true"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# NAT Gateway for private subnet outbound traffic
resource "aws_eip" "nat" {
  count  = length(var.availability_zones)
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  count         = length(var.availability_zones)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "hms-nat-${var.availability_zones[count.index]}"
    HIPAA = "true"
  }
  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "private" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "hms-private-rt-${var.availability_zones[count.index]}"
    HIPAA = "true"
  }
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Enable VPC Flow Logs for HIPAA compliance
resource "aws_flow_log" "vpc" {
  vpc_id           = aws_vpc.main.id
  log_destination_type = "cloud-watch-logs"
  log_group_name   = aws_cloudwatch_log_group.vpc_flow_logs.name
  traffic_type     = "ALL"

  tags = {
    Name = "hms-vpc-flow-logs"
    HIPAA = "true"
  }
}

resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/flow-logs/hms-${var.environment}"
  retention_in_days = 365  # HIPAA requirement: 1 year retention

  tags = {
    HIPAA = "true"
  }
}
