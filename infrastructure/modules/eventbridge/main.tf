variable "project" {}
variable "lambda_arn" {}

resource "aws_cloudwatch_event_bus" "this" {
  name = "${var.project}-events"
}

resource "aws_cloudwatch_event_rule" "all_events" {
  name           = "${var.project}-all-events"
  event_bus_name = aws_cloudwatch_event_bus.this.name
  event_pattern = jsonencode({
    source = ["ecommerce.storefront"]
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule           = aws_cloudwatch_event_rule.all_events.name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  arn            = var.lambda_arn
}

output "bus_name" {
  value = aws_cloudwatch_event_bus.this.name
}

output "rule_arn" {
  value = aws_cloudwatch_event_rule.all_events.arn
}
