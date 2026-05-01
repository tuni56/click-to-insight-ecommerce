variable "project" {}

resource "aws_iam_user" "grafana" {
  name = "${var.project}-grafana-reader"
  tags = { Project = var.project }
}

resource "aws_iam_user_policy" "grafana" {
  name = "${var.project}-grafana-cloudwatch-read"
  user = aws_iam_user.grafana.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:DescribeAlarms",
        "logs:DescribeLogGroups",
        "logs:GetLogEvents",
        "logs:StartQuery",
        "logs:GetQueryResults",
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_access_key" "grafana" {
  user = aws_iam_user.grafana.name
}

output "access_key_id" {
  value     = aws_iam_access_key.grafana.id
  sensitive = true
}

output "secret_access_key" {
  value     = aws_iam_access_key.grafana.secret
  sensitive = true
}
