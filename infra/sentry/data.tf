data "sentry_organization_integration" "slack" {
  organization = sentry_project.neoai_chat_backend.organization

  provider_key = "slack"
  name         = "株式会社neoAI"
}
