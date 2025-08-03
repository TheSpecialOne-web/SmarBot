module "azure_neoai" {
  source = "../modules/workload_identity"

  workload_identity_pool_id = "azure-neoai-dev"
  display_name              = "Azure neoAI Dev"
  description               = "Azureからの認証のためのWorkload Identity Pool"

  provider_id           = "azure-neoai-dev"
  provider_display_name = "azure-neoai-dev"
  provider_description  = "Azureからの認証のためのWorkload Identity Pool Provider"

  attribute_condition = null
  attribute_mapping = {
    "google.subject" = "assertion.sub"
  }

  oidc_allowed_audiences = [
    "cfa8b339-82a2-471a-a3c9-0fc0be7a4093"
  ]
  oidc_issuer_uri = "https://sts.windows.net/b09fd617-cb57-4990-8bc9-06593e54c81f/"
  oidc_jwks_json  = null
}

module "github" {
  source = "../modules/workload_identity"

  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions Pool"
  description               = "GitHub Actionsからの認証のためのWorkload Identity Pool"

  provider_id           = "neo-smart-chat"
  provider_display_name = "neo-smart-chat repository"
  provider_description  = "neo-smart-chat repositoryのためのWorkload Identity Pool Provider"

  attribute_condition = "assertion.repository_owner == 'neoAI-inc'"
  attribute_mapping = {
    "attribute.actor"            = "assertion.actor"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
    "google.subject"             = "assertion.sub"
  }

  oidc_allowed_audiences = []
  oidc_issuer_uri        = "https://token.actions.githubusercontent.com"
  oidc_jwks_json         = null
}
