variable "aws_region" {
  description = "Target AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for AWS resources"
  type        = string
  default     = "smartirrigate"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}
