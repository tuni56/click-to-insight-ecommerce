variable "project" {}
variable "lambda_role_name" {}

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project}-dlq"
  message_retention_seconds = 1209600 # 14 days
  tags                      = { Project = var.project }
}

resource "aws_iam_role_policy" "lambda_dlq" {
  name = "${var.project}-lambda-dlq-policy"
  role = var.lambda_role_name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = aws_sqs_queue.dlq.arn
    }]
  })
}

output "queue_arn" {
  value = aws_sqs_queue.dlq.arn
}

output "queue_url" {
  value = aws_sqs_queue.dlq.url
}

output "queue_name" {
  value = aws_sqs_queue.dlq.name
}
