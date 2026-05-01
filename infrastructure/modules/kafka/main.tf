variable "project" {}

# Confluent Cloud Kafka runs externally — no AWS resource to provision.
# Lambda connects via an MSK-compatible event source mapping using
# SASL_SSL credentials stored in AWS Secrets Manager.

resource "aws_secretsmanager_secret" "kafka_credentials" {
  name                    = "${var.project}-kafka-credentials"
  recovery_window_in_days = 0
  tags                    = { Project = var.project }
}

resource "aws_secretsmanager_secret_version" "kafka_credentials" {
  secret_id = aws_secretsmanager_secret.kafka_credentials.id
  secret_string = jsonencode({
    username = "REPLACE_WITH_API_KEY"
    password = "REPLACE_WITH_API_SECRET"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

output "secret_arn" {
  value = aws_secretsmanager_secret.kafka_credentials.arn
}

# topic_arn is not a real ARN for Confluent Cloud — we use a placeholder
# so the lambda module can reference it for the event source mapping.
output "topic_arn" {
  value = aws_secretsmanager_secret.kafka_credentials.arn
}
