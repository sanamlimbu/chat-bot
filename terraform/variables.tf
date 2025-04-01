variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-southeast-2"
}

variable "stage_name" {
  description = "Deployment stage name."
  type        = string
  default     = "prod"
}

variable "openai_api_key" {
  description = "OpenAI APi key"
  type        = string
}

variable "supabase_url" {
  description = "Supabase project url"
  type        = string
}

variable "supabase_service_key" {
  description = "Supabase service key"
  type        = string
}

variable "langchain_api_key" {
  description = "Langchain API key"
  type        = string
}

variable "langchain_project" {
  description = "Langchain project"
  type        = string
}

variable "langchain_tracing" {
  description = "AWS SNS topic."
  type        = bool
}

variable "telegram_bot_token" {
  description = "Telegram bot token"
  type        = string
}

variable "repo_name" {
  description = "AWS ECR repo name"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
}