resource "sentry_team" "neoai_inc" {
  name         = sentry_organization.neoai_inc.name
  organization = sentry_organization.neoai_inc.id
  slug         = sentry_organization.neoai_inc.slug
}
