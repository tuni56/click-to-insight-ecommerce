variable "project" {}
variable "account_id" {}

resource "aws_s3_bucket" "this" {
  bucket        = "${var.project}-events-lake-${var.account_id}"
  force_destroy = true
  tags          = { Project = var.project }
}

resource "aws_iam_role" "this" {
  name = "${var.project}-firehose-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "firehose.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "this" {
  name = "${var.project}-firehose-policy"
  role = aws_iam_role.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject", "s3:GetBucketLocation", "s3:ListBucket"]
      Resource = [aws_s3_bucket.this.arn, "${aws_s3_bucket.this.arn}/*"]
    }]
  })
}

resource "aws_kinesis_firehose_delivery_stream" "this" {
  name        = "${var.project}-events-to-s3"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn            = aws_iam_role.this.arn
    bucket_arn          = aws_s3_bucket.this.arn
    prefix              = "events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"
    error_output_prefix = "errors/"
    buffering_size      = 1
    buffering_interval  = 60
  }

  tags = { Project = var.project }
}

output "stream_name" {
  value = aws_kinesis_firehose_delivery_stream.this.name
}

output "stream_arn" {
  value = aws_kinesis_firehose_delivery_stream.this.arn
}

output "bucket_id" {
  value = aws_s3_bucket.this.id
}
