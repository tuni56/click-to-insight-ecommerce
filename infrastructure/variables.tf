variable "region" {
  description = "AWS region"
  default     = "us-east-2"
}

variable "project" {
  description = "Project name used for resource naming"
  default     = "click-to-insight"
}

variable "alert_email" {
  description = "Email for CloudWatch alarm notifications"
  default     = ""
}
