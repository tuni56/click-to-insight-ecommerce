variable "project" {}
variable "function_name" {}
variable "dlq_name" {}
variable "alert_email" {}

resource "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts"
  tags = { Project = var.project }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# --- Lambda errors alarm ---
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Lambda processing errors detected"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.function_name
  }

  tags = { Project = var.project }
}

# --- DLQ messages alarm ---
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project}-dlq-not-empty"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Dead letter queue has unprocessed messages"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = var.dlq_name
  }

  tags = { Project = var.project }
}

# --- Lambda throttles alarm ---
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${var.project}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Lambda is being throttled"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.function_name
  }

  tags = { Project = var.project }
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}
