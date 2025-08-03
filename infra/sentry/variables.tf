variable "dev_stg_env" {
  type = list(string)
  default = [
    "development",
    "staging",
  ]
}

variable "prd_env" {
  type = list(string)
  default = [
    "production",
    "production_ases",
    "production_ibk",
    "production_jp-bank",
    "production_jsbank",
    "production_kyuden",
    "production_nrtas-ana",
    "production_sbis-bank",
    "production_oss-bank",
  ]
}

variable "channels" {
  type = list(object({
    environment       = string
    target_identifier = string
    input_channel_id  = string
  }))
  default = [
    {
      environment       = "development",
      target_identifier = "5-neo-sc-notify-azure-dev",
      input_channel_id  = "C05U9UAM95Z"
    },
    {
      environment       = "staging",
      target_identifier = "5-neo-sc-notify-azure-stg",
      input_channel_id  = "C06JF4WE74G"
    },
    {
      environment       = "production",
      target_identifier = "5-neo-sc-notify-azure-prod",
      input_channel_id  = "C06HKMYEDCN"
    },
    {
      environment       = "production_ases",
      target_identifier = "5-neo-sc-notify-azure-neosc-ases"
      input_channel_id  = "C07S9DGG3L6"
    },
    {
      environment       = "production_ibk"
      target_identifier = "5-neo-sc-notify-azure-ibk"
      input_channel_id  = "C07A05Y7T0A"
    },
    {
      environment       = "production_jp-bank",
      target_identifier = "5-neo-sc-notify-azure-jp-bank"
      input_channel_id  = "C06M15H076F"
    },
    {
      environment       = "production_kyuden",
      target_identifier = "5-neo-sc-notify-azure-kyuden"
      input_channel_id  = "C0808KT7HAB"
    },
    {
      environment       = "production_jsbank",
      target_identifier = "5-neo-sc-notify-azure-jsbank"
      input_channel_id  = "C07BXT3V7PV"
    },
    {
      environment       = "production_nrtas-ana",
      target_identifier = "5-neo-sc-notify-azure-nrtas-ana"
      input_channel_id  = "C07FDUA37H7"
    },
    {
      environment       = "production_sbis-bank",
      target_identifier = "5-neo-sc-notify-azure-sbis-bank"
      input_channel_id  = "C07QM7KKS4X"
    },
    {
      environment       = "production_oss-bank",
      target_identifier = "5-neo-sc-notify-azure-oss-bank"
      input_channel_id  = "C088M46TFQU"
    },
  ]
}

variable "base_metric_alerts" {
  type = list(object({
    name  = string
    query = string
    triggers = list(object({
      label           = string
      alert_threshold = number
    }))
  }))

  default = [
    {
      name  = "GET: /backend-api/bots has a high p95 latency"
      query = "http.method:GET transaction:/backend-api/bots"
      triggers = [
        {
          label           = "critical"
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "GET: /backend-api/bots/<bot_id>/document-folders has a high p95 latency"
      query = "http.method:GET transaction:/backend-api/bots/<bot_id>/document-folders"
      triggers = [
        {
          label           = "critical"
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "GET: /backend-api/bots/<bot_id>/prompt-templates has a high p95 latency"
      query = "http.method:GET transaction:/backend-api/bots/<bot_id>/prompt-templates"
      triggers = [
        {
          label           = "critical"
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "GET: /backend-api/notifications has a high p95 latency"
      query = "http.method:GET transaction:/backend-api/notifications"
      triggers = [
        {
          label           = "critical",
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "GET: /backend-api/prompt-templates has a high p95 latency"
      query = "http.method:GET transaction:/backend-api/prompt-templates"
      triggers = [
        {
          label           = "critical"
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "GET: /backend-api/userinfo has a high p95 latency"
      query = "http.method:GET transaction:/backend-api/userinfo"
      triggers = [
        {
          label           = "critical",
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "GET: /backend-api/users/<user_id>/conversations has a high p95 latency"
      query = "http.method:GET transaction:/backend-api/users/<user_id>/conversations"
      triggers = [
        {
          label           = "critical",
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "POST: /backend-api/bots/<bot_id>/attachments has a high p95 latency"
      query = "http.method:POST transaction:/backend-api/bots/<bot_id>/attachments"
      triggers = [
        {
          label           = "critical",
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "POST: /backend-api/bots/<bot_id>/conversations has a high p95 latency"
      query = "http.method:POST transaction:/backend-api/bots/<bot_id>/conversations"
      triggers = [
        {
          label           = "critical",
          alert_threshold = 2000
        }
      ]
    },
    {
      name  = "POST: /backend-api/bots/<bot_id>/conversations/validate has a high p95 latency"
      query = "http.method:POST transaction:/backend-api/bots/<bot_id>/conversations/validate"
      triggers = [
        {
          label           = "critical",
          alert_threshold = 2000
        }
      ]
    },
  ]
}
