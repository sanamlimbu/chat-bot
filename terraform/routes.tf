resource "aws_apigatewayv2_route" "health" {
  operation_name = "health"
  api_id         = aws_apigatewayv2_api.lambda.id
  route_key      = "GET /health"
  target         = "integrations/${aws_apigatewayv2_integration.integration.id}"
}

resource "aws_apigatewayv2_route" "chat" {
  operation_name = "chat"
  api_id         = aws_apigatewayv2_api.lambda.id
  route_key      = "POST /chat"
  target         = "integrations/${aws_apigatewayv2_integration.integration.id}"
}

resource "aws_apigatewayv2_route" "upload" {
  operation_name = "upload"
  api_id         = aws_apigatewayv2_api.lambda.id
  route_key      = "POST /upload"
  target         = "integrations/${aws_apigatewayv2_integration.integration.id}"
}

resource "aws_apigatewayv2_route" "telegram_hook" {
  operation_name = "telegramHook"
  api_id         = aws_apigatewayv2_api.lambda.id
  route_key      = "POST /telegram-webhook"
  target         = "integrations/${aws_apigatewayv2_integration.integration.id}"
}