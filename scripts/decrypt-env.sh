#!/bin/bash

KEY_FILE="env-encryption-key"
GITHUB_TOKEN_FILE="github-token"

if [ ! -f "$KEY_FILE" ]; then
  echo "$KEY_FILE not found."
  echo "Please enter the encryption key:"
  read -s ENCRYPTION_KEY
  echo "$ENCRYPTION_KEY" >"$KEY_FILE"
fi

if [ ! -f "$GITHUB_TOKEN_FILE" ]; then
  echo "$GITHUB_TOKEN_FILE not found."
  echo "Please enter your GitHub Personal Access Token:"
  read -s GITHUB_TOKEN
  echo "$GITHUB_TOKEN" >"$GITHUB_TOKEN_FILE"
else
  GITHUB_TOKEN=$(cat "$GITHUB_TOKEN_FILE")
fi

decrypt_env() {
  local file=$1

  openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in "$file.enc" -out "$file" -pass file:"$KEY_FILE"

  if [ $? -eq 0 ]; then
    echo "Decryption successful. Decrypted file saved as $file"
  else
    echo "Decryption failed."
    exit 1
  fi

  sed -i '' "s/GITHUB_PERSONAL_ACCESS_TOKEN=.*/GITHUB_PERSONAL_ACCESS_TOKEN=\"$GITHUB_TOKEN\"/" "$file"

  if [ $? -eq 0 ]; then
    echo "GITHUB_PERSONAL_ACCESS_TOKEN updated in $file"
  else
    echo "Failed to update GITHUB_PERSONAL_ACCESS_TOKEN in $file"
    exit 1
  fi
}

decrypt_env ".env"
decrypt_env "./frontend/.env"
decrypt_env "./backend/.env"
decrypt_env "./function/.env"

echo "🎉 Decrypted env files"
