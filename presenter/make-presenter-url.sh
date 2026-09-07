#!/usr/bin/env bash
set -euo pipefail

PUBLIC_BASE="https://immich.piquot.eu/_presenter/"
PRESENTER_TOKEN="TOKEN_A_CONFIGURER"

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <url_de_partage_immich>"
  echo "Exemple:"
  echo "  $0 https://immich.piquot.eu/share/abc123"
  exit 1
fi

INPUT="$1"

SHARE_KEY="${INPUT##*/share/}"
SHARE_KEY="${SHARE_KEY%%\?*}"
SHARE_KEY="${SHARE_KEY%%\#*}"

if [ -z "$SHARE_KEY" ] || [ "$SHARE_KEY" = "$INPUT" ]; then
  echo "ERREUR : impossible d'extraire la clé de partage."
  echo "URL attendue : https://immich.piquot.eu/share/xxxxx"
  exit 1
fi

echo
echo "Lien visiteur :"
echo "${PUBLIC_BASE}?share=${SHARE_KEY}"

echo
echo "Lien présentateur :"
echo "${PUBLIC_BASE}?share=${SHARE_KEY}&presenter=${PRESENTER_TOKEN}"

echo
