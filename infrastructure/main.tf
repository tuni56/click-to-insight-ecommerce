terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

module "eventbridge" {
  source     = "./modules/eventbridge"
  project    = var.project
  lambda_arn = module.lambda.function_arn
}

module "dynamodb" {
  source  = "./modules/dynamodb"
  project = var.project
}

module "firehose" {
  source     = "./modules/firehose"
  project    = var.project
  account_id = local.account_id
}

module "lambda" {
  source          = "./modules/lambda"
  project         = var.project
  source_dir      = "${path.module}/../src/lambdas/process_event"
  table_name      = module.dynamodb.table_name
  table_arn       = module.dynamodb.table_arn
  firehose_name   = module.firehose.stream_name
  firehose_arn    = module.firehose.stream_arn
  eventbridge_arn = module.eventbridge.rule_arn
}

module "dashboard" {
  source        = "./modules/dashboard"
  project       = var.project
  function_name = module.lambda.function_name
  dashboard_body = file("${path.module}/../dashboards/cloudwatch-dashboard.json")
}
