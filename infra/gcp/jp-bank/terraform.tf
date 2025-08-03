terraform {
  required_providers {
    google = {
      version = "~> 6.0.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-neosc-dev"
    storage_account_name = "neosctfstatestorage"
    container_name       = "tfstate"
    key                  = "gcp/neo-sc-jp-bank/terraform.tfstate"
  }
}

provider "google" {
  project = "neosc-jp-bank"
}
