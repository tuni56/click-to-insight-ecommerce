variable "project" {}
variable "source_dir" {}
variable "table_name" {}
variable "table_arn" {}
variable "firehose_name" {}
variable "firehose_arn" {}
variable "kafka_topic_arn" {}
variable "kafka_bootstrap_servers" {
  default = ""
}
variable "dlq_arn" {
  default = ""
}

data "archive_file" "this" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/lambda.zip"
}

resource "aws_iam_role" "this" {
  name = "${var.project}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "this" {
  name = "${var.project}-lambda-policy"
  role = aws_iam_role.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = var.table_arn
      },
      {
        Effect   = "Allow"
        Action   = ["firehose:PutRecord"]
        Resource = var.firehose_arn
      },
      {
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = var.kafka_topic_arn
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "this" {
  function_name    = "${var.project}-process-event"
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.this.output_path
  source_code_hash = data.archive_file.this.output_base64sha256
  role             = aws_iam_role.this.arn

  environment {
    variables = {
      TABLE_NAME      = var.table_name
      FIREHOSE_STREAM = var.firehose_name
    }
  }

  dynamic "dead_letter_config" {
    for_each = var.dlq_arn != "" ? [1] : []
    content {
      target_arn = var.dlq_arn
    }
  }
}

# Self-managed Kafka (Confluent Cloud) event source mapping
resource "aws_lambda_event_source_mapping" "kafka" {
  count             = var.kafka_bootstrap_servers != "" ? 1 : 0
  function_name     = aws_lambda_function.this.arn
  event_source_arn  = null
  topics            = ["page_view", "cart_event", "purchase"]
  starting_position = "TRIM_HORIZON"
  batch_size        = 100

  self_managed_event_source {
    endpoints = {
      KAFKA_BOOTSTRAP_SERVERS = var.kafka_bootstrap_servers
    }
  }

  source_access_configuration {
    type = "SASL_SCRAM_512_AUTH"
    uri  = var.kafka_topic_arn
  }
}

output "function_arn" {
  value = aws_lambda_function.this.arn
}

output "function_name" {
  value = aws_lambda_function.this.function_name
}

output "role_name" {
  value = aws_iam_role.this.name
}
