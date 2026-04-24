variable "project" {}
variable "source_dir" {}
variable "table_name" {}
variable "table_arn" {}
variable "firehose_name" {}
variable "firehose_arn" {}
variable "eventbridge_arn" {}

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
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = var.eventbridge_arn
}

output "function_arn" {
  value = aws_lambda_function.this.arn
}

output "function_name" {
  value = aws_lambda_function.this.function_name
}
