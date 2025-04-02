locals {
  service_name = "chat-bot"
  package_path = "${path.module}/tf_generated/packages"
  archive_path = "${path.module}/tf_generated/${local.service_name}.zip"
}

locals {
  route_map = {
    "chat"             = "POST"
    "upload"           = "POST"
    "telegram-webhook" = "POST"
    "health"           = "GET"
  }
}
