locals {
  env = concat(var.dev_stg_env, var.prd_env)

  issue_alerts = flatten([
    for env in local.env : [
      {
        environment = env
        name        = "Error Alert (${env})"
        channel     = lookup({ for ch in var.channels : ch.environment => ch }, env)
      }
    ]
  ])
}

resource "sentry_issue_alert" "slack_notification" {
  for_each = { for al in local.issue_alerts : "${al.name}-${al.environment}" => al }

  organization = sentry_project.neoai_chat_backend.organization
  project      = sentry_project.neoai_chat_backend.id
  owner        = "team:${sentry_team.neoai_inc.internal_id}"
  name         = each.value.name
  environment  = each.value.environment
  action_match = "all"
  frequency    = 1440 # 24 hours
  actions = jsonencode([
    {
      id         = "sentry.integrations.slack.notify_action.SlackNotifyServiceAction"
      workspace  = "${parseint(data.sentry_organization_integration.slack.id, 10)}" # 株式会社neoAIのワークスペースID
      channel    = each.value.channel.target_identifier
      channel_id = each.value.channel.input_channel_id
    }
  ])
  conditions = jsonencode([
    {
      id   = "sentry.rules.conditions.first_seen_event.FirstSeenEventCondition"
      name = "A new issue is created"
    }
  ])
  filter_match = "all"
  filters = jsonencode([
    {
      attribute = "message"
      id        = "sentry.rules.filters.event_attribute.EventAttributeFilter"
      match     = "nc"
      name      = "The event's message value does not contain 400 Bad Request:"
      value     = "400 Bad Request:"
    },
    {
      attribute = "message"
      id        = "sentry.rules.filters.event_attribute.EventAttributeFilter"
      match     = "nc"
      name      = "The event's message value does not contain 404 Not Found:"
      value     = "404 Not Found:"
    }
  ])
}

resource "sentry_issue_alert" "new_issue" {
  name         = "Send a notification for new issues"
  organization = sentry_project.neoai_chat_backend.organization
  project      = sentry_project.neoai_chat_backend.id
  action_match = "all"
  filter_match = "all"
  frequency    = 30 # 30 minutes
  actions = jsonencode([
    {
      fallthroughType  = "ActiveMembers"
      id               = "sentry.mail.actions.NotifyEmailAction"
      name             = "Send a notification to IssueOwners and if none can be found then send a notification to ActiveMembers"
      targetIdentifier = null
      targetType       = "IssueOwners"
    }
  ])
  conditions = jsonencode([
    {
      id   = "sentry.rules.conditions.first_seen_event.FirstSeenEventCondition"
      name = "A new issue is created"
    }
  ])
}
