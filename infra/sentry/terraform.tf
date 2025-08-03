terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    sentry = {
      source  = "jianyuan/sentry"
      version = "~> 0.9"
    }
  }

  required_version = ">=1.9.0"

  backend "azurerm" {
    resource_group_name  = "rg-neosc-dev"
    storage_account_name = "neosctfstatestorage"
    container_name       = "tfstate"
    key                  = "sentry/terraform.tfstate"
  }
}

# トークンは環境変数から取得する
# ref: https://learn.microsoft.com/ja-jp/azure/developer/terraform/store-state-in-azure-storage?tabs=azure-cli#3-configure-terraform-backend-state
provider "azurerm" {
  features {}
}

# トークンは環境変数から取得する
# ref: https://registry.terraform.io/providers/jianyuan/sentry/latest/docs#authentication
provider "sentry" {}
