terraform {
  cloud {
    organization = "sanam-default-org"
    workspaces {
      name = "rag-chat-bot"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92.0"
    }
  }

  required_version = "~> 1.11.3"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Name  = local.service_name
      Stage = var.stage_name
    }
  }
}

data "aws_ecr_repository" "repo" {
  name = var.repo_name
}

resource "aws_lambda_function" "function" {
  function_name = local.service_name
  description   = "Chat bot API."
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${data.aws_ecr_repository.repo.repository_url}:${var.image_tag}"

  memory_size   = 2048
  architectures = ["x86_64"]

  timeout = 900

  environment {
    variables = {
      "OPENAI_API_Key"       = var.openai_api_key,
      "SUPABASE_URL"         = var.supabase_url,
      "SUPABASE_SERVICE_KEY" = var.supabase_service_key,
      "LANGCHAIN_API_KEY"    = var.langchain_api_key,
      "LANGCHAIN_PROJECT"    = var.langchain_project,
      "LANGCHAIN_TRACING"    = var.langchain_tracing,
      "TELEGRAM_BOT_TOKEN"   = var.telegram_bot_token
    }
  }
}

resource "aws_cloudwatch_log_group" "log_group" {
  name              = "/aws/lambda/${aws_lambda_function.function.function_name}"
  retention_in_days = 30
}

resource "aws_iam_role" "lambda_exec" {
  name        = "${local.service_name}-lambda-role"
  description = "Allow lambda to access AWS services or resources."

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_apigatewayv2_api" "lambda" {
  name          = "chat-bot-gateway"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id = aws_apigatewayv2_api.lambda.id

  name        = "prod"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn

    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp                = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      protocol                = "$context.protocol"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
      }
    )
  }
}

resource "aws_apigatewayv2_integration" "integration" {
  api_id = aws_apigatewayv2_api.lambda.id

  integration_uri    = aws_lambda_function.function.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "route" {
  api_id = aws_apigatewayv2_api.lambda.id

  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.integration.id}"
}


resource "aws_cloudwatch_log_group" "api_gw" {
  name = "/aws/api_gw/${aws_apigatewayv2_api.lambda.name}"

  retention_in_days = 30
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.function.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.lambda.execution_arn}/*/*"
}

output "lambda_invoke_url" {
  value = "${aws_apigatewayv2_api.lambda.api_endpoint}/${aws_apigatewayv2_stage.prod.name}/"
}