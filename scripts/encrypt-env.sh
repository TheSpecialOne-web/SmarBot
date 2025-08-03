#!/bin/bash

KEY_FILE="env-encryption-key"

if [ $# -eq 0 ]; then
  echo "Usage: $0 <package1> [package2] ..."
  echo "Valid packages: all, root, frontend, backend, function"
  exit 1
fi

if [ ! -f "$KEY_FILE" ]; then
  echo "$KEY_FILE not found."
  echo "Please enter the encryption key:"
  read -s ENCRYPTION_KEY
  echo "$ENCRYPTION_KEY" >"$KEY_FILE"
fi

encrypt_env() {
  local file=$1

  if [ ! -f "$file" ]; then
    echo "Error: Input file '$file' not found."
    exit 1
  fi

  sed 's/GITHUB_PERSONAL_ACCESS_TOKEN=".*"/GITHUB_PERSONAL_ACCESS_TOKEN=""/' "$file" >"$file.tmp"
  openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 -in "$file.tmp" -out "$file.enc" -pass file:"$KEY_FILE"

  if [ $? -eq 0 ]; then
    echo "Encryption successful. Encrypted file saved as $file.enc"
    rm "$file.tmp"
  else
    echo "Encryption failed."
    rm "$file.tmp"
    exit 1
  fi
}

process_package() {
  local package=$1
  case $package in
  all)
    encrypt_env ".env"
    encrypt_env "./frontend/.env"
    encrypt_env "./backend/.env"
    encrypt_env "./function/.env"
    ;;
  root)
    encrypt_env ".env"
    ;;
  frontend)
    encrypt_env "./frontend/.env"
    ;;
  backend)
    encrypt_env "./backend/.env"
    ;;
  function)
    encrypt_env "./function/.env"
    ;;
  *)
    echo "Error: Invalid package '$package'. Valid packages are: all, root, frontend, backend, function"
    exit 1
    ;;
  esac
}

for package in "$@"; do
  process_package "$package"
done

echo "🎉 Encrypted env files"
