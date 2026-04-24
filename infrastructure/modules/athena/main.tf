variable "project" {}
variable "bucket_id" {}
variable "account_id" {}

resource "aws_s3_bucket" "athena_results" {
  bucket        = "${var.project}-athena-results-${var.account_id}"
  force_destroy = true
  tags          = { Project = var.project }
}

resource "aws_athena_workgroup" "this" {
  name          = var.project
  force_destroy = true

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.id}/results/"
    }
  }
}

resource "aws_glue_catalog_database" "this" {
  name = replace(var.project, "-", "_")
}

resource "aws_glue_catalog_table" "events" {
  name          = "events"
  database_name = aws_glue_catalog_database.this.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "json"
    EXTERNAL         = "TRUE"
  }

  storage_descriptor {
    location      = "s3://${var.bucket_id}/events/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
    }

    columns {
      name = "event_type"
      type = "string"
    }
    columns {
      name = "event_id"
      type = "string"
    }
    columns {
      name = "user_id"
      type = "string"
    }
    columns {
      name = "timestamp"
      type = "string"
    }
    columns {
      name = "page_url"
      type = "string"
    }
    columns {
      name = "product_id"
      type = "string"
    }
    columns {
      name = "product_name"
      type = "string"
    }
    columns {
      name = "action"
      type = "string"
    }
    columns {
      name = "quantity"
      type = "int"
    }
    columns {
      name = "unit_price"
      type = "double"
    }
    columns {
      name = "order_id"
      type = "string"
    }
    columns {
      name = "total_amount"
      type = "double"
    }
    columns {
      name = "currency"
      type = "string"
    }
    columns {
      name = "processed_at"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- Named Queries (saved in Athena console) ---

resource "aws_athena_named_query" "revenue_per_hour" {
  name      = "Revenue per hour"
  workgroup = aws_athena_workgroup.this.name
  database  = aws_glue_catalog_database.this.name
  query     = <<-EOQ
    SELECT
      date_trunc('hour', from_iso8601_timestamp(timestamp)) AS hour,
      SUM(total_amount) AS total_revenue,
      COUNT(*) AS purchase_count
    FROM events
    WHERE event_type = 'purchase'
    GROUP BY 1
    ORDER BY 1 DESC
    LIMIT 24
  EOQ
}

resource "aws_athena_named_query" "top_products_in_cart" {
  name      = "Top products added to cart"
  workgroup = aws_athena_workgroup.this.name
  database  = aws_glue_catalog_database.this.name
  query     = <<-EOQ
    SELECT
      product_name,
      product_id,
      COUNT(*) AS times_added
    FROM events
    WHERE event_type = 'cart_event' AND action = 'add'
    GROUP BY product_name, product_id
    ORDER BY times_added DESC
    LIMIT 10
  EOQ
}

resource "aws_athena_named_query" "funnel_analysis" {
  name      = "Conversion funnel"
  workgroup = aws_athena_workgroup.this.name
  database  = aws_glue_catalog_database.this.name
  query     = <<-EOQ
    SELECT
      event_type,
      COUNT(DISTINCT user_id) AS unique_users,
      COUNT(*) AS total_events
    FROM events
    GROUP BY event_type
    ORDER BY total_events DESC
  EOQ
}

resource "aws_athena_named_query" "events_per_minute" {
  name      = "Events per minute by type"
  workgroup = aws_athena_workgroup.this.name
  database  = aws_glue_catalog_database.this.name
  query     = <<-EOQ
    SELECT
      date_trunc('minute', from_iso8601_timestamp(timestamp)) AS minute,
      event_type,
      COUNT(*) AS event_count
    FROM events
    GROUP BY 1, 2
    ORDER BY 1 DESC, 3 DESC
    LIMIT 100
  EOQ
}

output "workgroup" {
  value = aws_athena_workgroup.this.name
}

output "database" {
  value = aws_glue_catalog_database.this.name
}
