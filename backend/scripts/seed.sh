#!/bin/bash

DEFAULT_TENANT_NAME="neoAI inc."
read -p "tenant_name: (default: $DEFAULT_TENANT_NAME) " TENANT_NAME
TENANT_NAME=${TENANT_NAME:-"$DEFAULT_TENANT_NAME"}

read -p "tenant_alias: (lowercase letters, numbers and hyphens) " TENANT_ALIAS
if [ -z "$TENANT_ALIAS" ]; then
  echo "tenant_alias is required"
  exit 1
fi

read -p "allow_foreign_region: (default: true) " ALLOW_FOREIGN_REGION
ALLOW_FOREIGN_REGION=${ALLOW_FOREIGN_REGION:-"true"}
if [ "$ALLOW_FOREIGN_REGION" != "true" ] && [ "$ALLOW_FOREIGN_REGION" != "false" ]; then
  echo "allow_foreign_region must be true or false"
  exit 1
fi

read -p "use_gcp: (default: false) " USE_GCP
USE_GCP=${USE_GCP:-"false"}
if [ "$USE_GCP" != "true" ] && [ "$USE_GCP" != "false" ]; then
  echo "use_gcp must be true or false"
  exit 1
fi

read -p "enable_document_intelligence: (default: false) " ENABLE_DOCUMENT_INTELLIGENCE
ENABLE_DOCUMENT_INTELLIGENCE=${ENABLE_DOCUMENT_INTELLIGENCE:-"false"}
if [ "$ENABLE_DOCUMENT_INTELLIGENCE" != "true" ] && [ "$ENABLE_DOCUMENT_INTELLIGENCE" != "false" ]; then
  echo "enable_document_intelligence must be true or false"
  exit 1
fi

read -p "admin_name: (default: admin) " ADMIN_NAME
ADMIN_NAME=${ADMIN_NAME:-"admin"}

read -p "admin_email: " ADMIN_EMAIL
if [ -z "$ADMIN_EMAIL" ]; then
  echo "admin_email is required"
  exit 1
fi

echo
echo "tenant_name: $TENANT_NAME"
echo "tenant_alias: $TENANT_ALIAS"
echo "allow_foreign_region: $ALLOW_FOREIGN_REGION"
echo "use_gcp: $USE_GCP"
echo "enable_document_intelligence: $ENABLE_DOCUMENT_INTELLIGENCE"
echo "admin_name: $ADMIN_NAME"
echo "admin_email: $ADMIN_EMAIL"
read -p "The above values will be used to init app. Continue? (Y/n)" confirm_create
if [ "$confirm_create" == "n" ]; then
  echo "Aborted"
  exit 1
fi

docker compose exec api poetry run python -m api.commands.init_app \
  --tenant-name "$TENANT_NAME" \
  --tenant-alias "$TENANT_ALIAS" \
  --allow-foreign-region $ALLOW_FOREIGN_REGION \
  --enable-document-intelligence $ENABLE_DOCUMENT_INTELLIGENCE \
  --use-gcp $USE_GCP \
  --enable-document-intelligence $ENABLE_DOCUMENT_INTELLIGENCE \
  --admin-name "$ADMIN_NAME" \
  --admin-email "$ADMIN_EMAIL"

echo "🎉 Initialized app"
