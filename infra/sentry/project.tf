resource "sentry_project" "neoai_chat_backend" {
  name         = "neoai-chat-backend"
  organization = sentry_organization.neoai_inc.id
  platform     = "python-fastapi"
  slug         = "neoai-chat-backend"
  teams        = [sentry_team.neoai_inc.id]
}

resource "sentry_project" "neoai_chat_frontend" {
  name         = "neoai-chat-frontend"
  organization = sentry_organization.neoai_inc.id
  platform     = "javascript-react"
  slug         = "neoai-chat-frontend"
  teams        = [sentry_team.neoai_inc.id]
}
