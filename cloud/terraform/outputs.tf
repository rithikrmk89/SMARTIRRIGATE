output "raw_bucket_name" {
  description = "S3 Raw Bucket Name"
  value       = aws_s3_bucket.raw_bucket.id
}

output "processed_bucket_name" {
  description = "S3 Processed Bucket Name"
  value       = aws_s3_bucket.processed_bucket.id
}

output "models_bucket_name" {
  description = "S3 Models Artefact Bucket Name"
  value       = aws_s3_bucket.models_bucket.id
}

output "lambda_function_arn" {
  description = "Data Processor Lambda ARN"
  value       = aws_lambda_function.data_processor.arn
}

output "sagemaker_role_arn" {
  description = "SageMaker Execution Role ARN"
  value       = aws_iam_role.sagemaker_role.arn
}
