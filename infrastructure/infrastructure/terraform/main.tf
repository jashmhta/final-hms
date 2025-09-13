module "vpc" {
  source = "./modules/vpc"

  vpc_cidr           = var.vpc_cidr
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
  availability_zones = var.availability_zones
}

module "database" {
  source = "./modules/database"

  vpc_id          = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_username     = var.db_username
  db_password     = var.db_password
  db_instance_class = var.db_instance_class
}

module "ecs" {
  source = "./modules/ecs"

  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  db_endpoint           = module.database.db_endpoint
  db_username           = var.db_username
  db_password           = var.db_password
  cluster_name          = var.cluster_name
}

module "security" {
  source = "./modules/security"

  vpc_id = module.vpc.vpc_id
  cluster_arn = module.ecs.cluster_arn
}
