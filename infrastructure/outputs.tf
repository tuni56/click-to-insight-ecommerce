output "event_bus_name" {
  value = module.eventbridge.bus_name
}

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
