variable "project" {}
variable "function_name" {}
variable "dashboard_body" {}

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = "${var.project}-realtime"
  dashboard_body = var.dashboard_body
}
