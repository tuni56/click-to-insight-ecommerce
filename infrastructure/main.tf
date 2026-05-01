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

module "kafka" {
  source  = "./modules/kafka"
  project = var.project
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
  kafka_topic_arn = module.kafka.topic_arn
  dlq_arn         = module.dlq.queue_arn
}

module "dlq" {
  source           = "./modules/dlq"
  project          = var.project
  lambda_role_name = module.lambda.role_name
}

module "athena" {
  source     = "./modules/athena"
  project    = var.project
  bucket_id  = module.firehose.bucket_id
  account_id = local.account_id
}

module "grafana_iam" {
  source  = "./modules/grafana_iam"
  project = var.project
}

module "alarms" {
  count         = var.alert_email != "" ? 1 : 0
  source        = "./modules/alarms"
  project       = var.project
  function_name = module.lambda.function_name
  dlq_name      = module.dlq.queue_name
  alert_email   = var.alert_email
}
