# Data sources for existing resources that might conflict
# This file helps avoid resource conflicts by using existing resources

# Try to use existing CloudWatch log group for FluentBit
data "aws_cloudwatch_log_group" "existing_fluentbit" {
  count = var.enable_fluentbit_logging ? 1 : 0
  name  = "/${local.name}/aws-fluentbit-logs"
}

# Check if S3 bucket already exists for FluentBit (commented out to avoid errors)
# data "aws_s3_bucket" "existing_app_data" {
#   count  = var.enable_s3_bucket ? 1 : 0
#   bucket = "${local.name}-app-data"
# }