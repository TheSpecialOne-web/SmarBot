resource "google_iam_workload_identity_pool" "workload_identity_pool" {
  workload_identity_pool_id = var.workload_identity_pool_id
  display_name              = var.display_name
  description               = var.description
  disabled                  = var.disabled
}

resource "google_iam_workload_identity_pool_provider" "workload_identity_pool_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.workload_identity_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = var.provider_id
  display_name                       = var.provider_display_name
  description                        = var.provider_description
  disabled                           = var.disabled
  attribute_condition                = var.attribute_condition
  attribute_mapping                  = var.attribute_mapping

  oidc {
    allowed_audiences = var.oidc_allowed_audiences
    issuer_uri        = var.oidc_issuer_uri
    jwks_json         = var.oidc_jwks_json
  }
}
