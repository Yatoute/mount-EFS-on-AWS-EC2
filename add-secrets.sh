#!/bin/bash

# Fonction pour lire un fichier .env et ajouter chaque variable comme secret à github
add_secrets_from_env() {
  local env_file=$1
  # Lire chaque ligne du fichier .env
  while IFS= read -r line; do
    # Ignorer les lignes vides et les commentaires
    if [[ ! "$line" =~ ^[[:space:]]*# && -n "$line" ]]; then
      # Extraire le nom et la valeur de la variable
      var_name=$(echo "$line" | cut -d '=' -f 1)
      var_value=$(echo "$line" | cut -d '=' -f 2-)

      # Enlever les guillemets autour de la valeur (si présents)
      var_value=$(echo "$var_value" | sed 's/^"//;s/"$//')

      # Ajouter la variable comme secret GitHub
      gh secret set "$var_name" --body "$var_value"
      echo "Added secret $var_name"
    fi
  done < "$env_file"
}

# Se connecter
gh auth login

# Appeler la fonction pour chaque fichier .env
add_secrets_from_env "./.env"
