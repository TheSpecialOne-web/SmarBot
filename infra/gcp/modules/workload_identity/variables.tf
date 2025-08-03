variable "workload_identity_pool_id" {
  type = string
}

variable "display_name" {
  type = string
}

variable "description" {
  type = string
}

variable "disabled" {
  type    = bool
  default = false
}

variable "provider_id" {
  type = string
}

variable "provider_display_name" {
  type = string
}

variable "provider_description" {
  type = string
}

variable "attribute_condition" {
  type    = string
  default = null
}

variable "attribute_mapping" {
  type = map(string)
}

variable "oidc_allowed_audiences" {
  type    = list(string)
  default = []
}

variable "oidc_issuer_uri" {
  type = string
}

variable "oidc_jwks_json" {
  type    = string
  default = null
}
