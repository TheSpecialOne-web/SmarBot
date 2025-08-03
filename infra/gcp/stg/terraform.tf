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
    key                  = "gcp/neo-sc-stg/terraform.tfstate"
  }
}

provider "google" {
  project = "neosc-stg"
}
