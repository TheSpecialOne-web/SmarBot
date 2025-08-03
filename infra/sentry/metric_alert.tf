locals {
  alerts = flatten([
    for env in var.prd_env : [
      for base_alert in var.base_metric_alerts : merge(base_alert, {
        environment = env
        name        = "${base_alert.name} - ${env}"
        channel     = lookup({ for ch in var.channels : ch.environment => ch }, env)
      })
    ]
  ])
}

resource "sentry_metric_alert" "p95_transaction_duration" {
  for_each = { for al in local.alerts : "${al.name}" => al }

  organization   = sentry_project.neoai_chat_backend.organization
  project        = sentry_project.neoai_chat_backend.id
  name           = each.value.name
  environment    = each.value.environment
  query          = each.value.query
  dataset        = "transactions"
  event_types    = ["transaction"]
  aggregate      = "p95(transaction.duration)"
  time_window    = 1
  threshold_type = 0

  dynamic "trigger" {
    for_each = { for tr in each.value.triggers : tr.label => tr }
    content {
      alert_threshold = trigger.value.alert_threshold
      label           = trigger.value.label
      threshold_type  = 0

      action {
        type              = "slack"
        target_type       = "specific"
        target_identifier = each.value.channel.target_identifier
        input_channel_id  = each.value.channel.input_channel_id
        integration_id    = data.sentry_organization_integration.slack.id
      }
    }
  }
}
