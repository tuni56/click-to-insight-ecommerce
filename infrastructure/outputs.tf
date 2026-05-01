output "lambda_function" {
  value = module.lambda.function_name
}

output "dynamodb_table" {
  value = module.dynamodb.table_name
}

output "s3_bucket" {
  value = module.firehose.bucket_id
}

output "firehose_stream" {
  value = module.firehose.stream_name
}

output "dlq_url" {
  value = module.dlq.queue_url
}

output "athena_workgroup" {
  value = module.athena.workgroup
}

output "athena_database" {
  value = module.athena.database
}

output "grafana_iam_access_key" {
  value     = module.grafana_iam.access_key_id
  sensitive = true
}

output "grafana_iam_secret_key" {
  value     = module.grafana_iam.secret_access_key
  sensitive = true
}
